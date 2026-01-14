"""In-memory job queue for HWP conversion"""
import threading
import uuid
from datetime import datetime
from typing import Dict, Optional, List
from dataclasses import dataclass, field

from .models import JobStatus


@dataclass
class Job:
    """Internal job representation"""
    job_id: str
    source_filename: str
    source_path: str
    output_path: Optional[str] = None
    status: JobStatus = JobStatus.PENDING
    created_at: datetime = field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None
    error: Optional[str] = None


class JobQueue:
    """Thread-safe in-memory job queue"""
    
    def __init__(self):
        self._jobs: Dict[str, Job] = {}
        self._lock = threading.Lock()
    
    def add_job(self, source_filename: str, source_path: str) -> Job:
        """Add a new job to the queue"""
        job_id = str(uuid.uuid4())
        job = Job(
            job_id=job_id,
            source_filename=source_filename,
            source_path=source_path,
        )
        with self._lock:
            self._jobs[job_id] = job
        return job
    
    def get_job(self, job_id: str) -> Optional[Job]:
        """Get job by ID"""
        with self._lock:
            return self._jobs.get(job_id)
    
    def update_status(
        self, 
        job_id: str, 
        status: JobStatus, 
        output_path: Optional[str] = None,
        error: Optional[str] = None
    ) -> bool:
        """Update job status"""
        with self._lock:
            job = self._jobs.get(job_id)
            if not job:
                return False
            job.status = status
            if output_path:
                job.output_path = output_path
            if error:
                job.error = error
            if status in (JobStatus.COMPLETED, JobStatus.FAILED):
                job.completed_at = datetime.now()
            return True
    
    def get_next_pending(self) -> Optional[Job]:
        """Get the oldest pending job"""
        with self._lock:
            pending = [j for j in self._jobs.values() if j.status == JobStatus.PENDING]
            if not pending:
                return None
            # Sort by created_at and return oldest
            pending.sort(key=lambda x: x.created_at)
            return pending[0]
    
    def get_all_jobs(self) -> List[Job]:
        """Get all jobs (for debugging/admin)"""
        with self._lock:
            return list(self._jobs.values())
    
    def clear(self) -> None:
        """Clear all jobs (for testing)"""
        with self._lock:
            self._jobs.clear()


# Global queue instance
job_queue = JobQueue()
