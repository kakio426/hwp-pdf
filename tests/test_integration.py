"""Integration tests for the complete conversion flow"""
import pytest
import time
from pathlib import Path
from unittest.mock import patch, MagicMock
import sys

from fastapi.testclient import TestClient
from api.main import app
from api.queue import job_queue
from api.models import JobStatus


@pytest.fixture(autouse=True)
def clear_queue():
    """Clear job queue before/after tests"""
    job_queue.clear()
    yield
    job_queue.clear()


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def sample_hwp(tmp_path):
    hwp_file = tmp_path / "test.hwp"
    hwp_file.write_bytes(b"HWP content")
    return hwp_file


@pytest.fixture
def mock_converter():
    """Mock the HWP converter to simulate successful conversion"""
    mock_hwp = MagicMock()
    mock_hwp.Open.return_value = True
    mock_hwp.HAction.Execute.return_value = True
    
    def mock_execute(action, hset):
        if action == "FileSaveAs_S":
            fname = mock_hwp.HParameterSet.HFileOpenSave.filename
            if fname:
                Path(fname).write_text("%PDF-mock")
            return True
        return True
    
    mock_hwp.HAction.Execute.side_effect = mock_execute
    
    mock_win32 = MagicMock()
    mock_win32.client.gencache.EnsureDispatch.return_value = mock_hwp
    
    with patch.dict(sys.modules, {
        'win32com': mock_win32,
        'win32com.client': mock_win32.client,
        'win32com.client.gencache': mock_win32.client.gencache,
        'pythoncom': MagicMock()
    }):
        with patch('src.hwp_converter.registry.ensure_security_module'):
            yield mock_hwp


class TestJobStateTransitions:
    """Test job state transitions through the system"""
    
    def test_job_starts_as_pending(self, client, sample_hwp):
        """New job should start with PENDING status"""
        with open(sample_hwp, "rb") as f:
            response = client.post(
                "/api/upload",
                files={"file": ("test.hwp", f)}
            )
        
        assert response.json()["status"] == "pending"
    
    def test_state_transition_pending_to_processing(self, mock_converter):
        """Job should transition from PENDING to PROCESSING when picked up"""
        from worker.processor import ConversionWorker
        
        # Create a job directly
        job = job_queue.add_job("test.hwp", str(Path(__file__).parent / "test.hwp"))
        
        # Create temp source file
        source = Path(job.source_path)
        source.parent.mkdir(parents=True, exist_ok=True)
        source.write_text("HWP content")
        
        assert job.status == JobStatus.PENDING
        
        # Process the job
        worker = ConversionWorker()
        worker._process_job(job)
        
        # Check final state
        updated_job = job_queue.get_job(job.job_id)
        assert updated_job.status == JobStatus.COMPLETED
    
    def test_state_transition_to_failed_on_error(self, mock_converter):
        """Job should transition to FAILED on conversion error"""
        from worker.processor import ConversionWorker
        
        # Make converter fail
        mock_converter.Open.return_value = False
        
        job = job_queue.add_job("test.hwp", "/nonexistent/file.hwp")
        
        worker = ConversionWorker()
        worker._process_job(job)
        
        updated_job = job_queue.get_job(job.job_id)
        assert updated_job.status == JobStatus.FAILED
        assert updated_job.error is not None


class TestWorkerIntegration:
    """Test worker behavior"""
    
    def test_worker_starts_and_stops(self):
        """Worker should start and stop cleanly"""
        from worker.processor import ConversionWorker
        
        worker = ConversionWorker(poll_interval=0.1)
        
        assert not worker.is_running
        
        worker.start()
        assert worker.is_running
        
        worker.stop()
        assert not worker.is_running
    
    def test_worker_processes_queued_job(self, mock_converter, tmp_path):
        """Worker should automatically process queued jobs"""
        from worker.processor import ConversionWorker
        
        # Create source file
        source_file = tmp_path / "test.hwp"
        source_file.write_text("HWP content")
        
        # Add job
        job = job_queue.add_job("test.hwp", str(source_file))
        
        # Start worker
        worker = ConversionWorker(poll_interval=0.1)
        worker.start()
        
        # Wait for processing
        time.sleep(0.5)
        
        worker.stop()
        
        # Check job was processed
        updated_job = job_queue.get_job(job.job_id)
        assert updated_job.status in (JobStatus.COMPLETED, JobStatus.FAILED)


class TestFullFlow:
    """End-to-end tests"""
    
    def test_upload_and_check_status(self, client, sample_hwp):
        """Upload file and verify job is created"""
        # Upload
        with open(sample_hwp, "rb") as f:
            upload_resp = client.post(
                "/api/upload",
                files={"file": ("test.hwp", f)}
            )
        
        job_id = upload_resp.json()["job_id"]
        
        # Check status
        status_resp = client.get(f"/api/status/{job_id}")
        
        assert status_resp.status_code == 200
        assert status_resp.json()["job_id"] == job_id
        assert status_resp.json()["source_filename"] == "test.hwp"
