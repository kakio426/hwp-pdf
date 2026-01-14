"""Background worker for processing HWP to PDF conversions"""
import logging
import threading
import time
from pathlib import Path
from typing import Optional

from api.queue import job_queue, Job
from api.models import JobStatus
from src.hwp_converter import HwpToPdfConverter, HwpConverterError
from src.odt_converter.core import OdtToPdfConverter, OdtConversionError

logger = logging.getLogger(__name__)


class ConversionWorker:
    """
    Background worker that polls the job queue and processes conversions.
    """
    
    def __init__(self, poll_interval: float = 1.0, timeout: int = 30):
        self.poll_interval = poll_interval
        self.timeout = timeout
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._lock = threading.Lock()
    
    def start(self) -> None:
        """Start the worker thread"""
        with self._lock:
            if self._running:
                logger.warning("Worker is already running")
                return
            
            self._running = True
            self._thread = threading.Thread(target=self._run, daemon=True)
            self._thread.start()
            logger.info("Conversion worker started")
    
    def stop(self) -> None:
        """Stop the worker thread"""
        with self._lock:
            if not self._running:
                return
            
            self._running = False
            logger.info("Stopping conversion worker...")
        
        if self._thread:
            self._thread.join(timeout=5)
            logger.info("Conversion worker stopped")
    
    def _run(self) -> None:
        """Main worker loop"""
        while self._running:
            try:
                job = job_queue.get_next_pending()
                if job:
                    self._process_job(job)
                else:
                    time.sleep(self.poll_interval)
            except Exception as e:
                logger.exception(f"Unexpected error in worker loop: {e}")
                time.sleep(self.poll_interval)
    
    def _process_job(self, job: Job) -> None:
        """Process a single job"""
        logger.info(f"Processing job {job.job_id}: {job.source_filename}")
        
        # Update status to processing
        job_queue.update_status(job.job_id, JobStatus.PROCESSING)
        
        try:
            # Determine output path
            source_path = Path(job.source_path)
            output_path = source_path.parent / "output.pdf"
            ext = source_path.suffix.lower()
            
            # Perform conversion based on type
            if ext in ('.hwp', '.hwpx'):
                with HwpToPdfConverter(timeout=self.timeout) as converter:
                    result_path = converter.convert(str(source_path), str(output_path))
            elif ext in ('.odt', '.docx'):
                 converter = OdtToPdfConverter()
                 result_path = converter.convert(str(source_path), str(output_path))
            else:
                raise ValueError(f"Unsupported file type: {ext}")
            
            # Update status to completed
            job_queue.update_status(
                job.job_id, 
                JobStatus.COMPLETED, 
                output_path=result_path
            )
            logger.info(f"Job {job.job_id} completed: {result_path}")
            
        except (HwpConverterError, OdtConversionError) as e:
            logger.error(f"Job {job.job_id} failed: {e}")
            job_queue.update_status(
                job.job_id, 
                JobStatus.FAILED, 
                error=str(e)
            )
        except Exception as e:
            logger.exception(f"Unexpected error processing job {job.job_id}")
            job_queue.update_status(
                job.job_id, 
                JobStatus.FAILED, 
                error=f"Unexpected error: {e}"
            )
    
    @property
    def is_running(self) -> bool:
        """Check if worker is running"""
        return self._running


# Global worker instance
worker = ConversionWorker()
