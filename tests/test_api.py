"""API endpoint tests using FastAPI TestClient"""
import pytest
from pathlib import Path
from fastapi.testclient import TestClient

from api.main import app
from api.queue import job_queue
from api.models import JobStatus


@pytest.fixture(autouse=True)
def clear_queue():
    """Clear the job queue before each test"""
    job_queue.clear()
    yield
    job_queue.clear()


@pytest.fixture
def client():
    """Create test client"""
    return TestClient(app)


@pytest.fixture
def sample_hwp_file(tmp_path):
    """Create a sample HWP file for testing"""
    hwp_file = tmp_path / "sample.hwp"
    hwp_file.write_bytes(b"HWP Document Format")
    return hwp_file


class TestUploadEndpoint:
    """Tests for POST /api/upload"""
    
    def test_upload_hwp_file(self, client, sample_hwp_file):
        """Test successful HWP file upload"""
        with open(sample_hwp_file, "rb") as f:
            response = client.post(
                "/api/upload",
                files={"file": ("test.hwp", f, "application/octet-stream")}
            )
        
        assert response.status_code == 200
        data = response.json()
        assert "job_id" in data
        assert data["status"] == "pending"
        assert "test.hwp" in data["message"]
    
    def test_upload_hwpx_file(self, client, tmp_path):
        """Test HWPX file upload is accepted"""
        hwpx_file = tmp_path / "sample.hwpx"
        hwpx_file.write_bytes(b"HWPX Document")
        
        with open(hwpx_file, "rb") as f:
            response = client.post(
                "/api/upload",
                files={"file": ("test.hwpx", f, "application/octet-stream")}
            )
        
        assert response.status_code == 200
        assert response.json()["status"] == "pending"
    
    def test_upload_invalid_file_type(self, client, tmp_path):
        """Test that non-HWP files are rejected"""
        txt_file = tmp_path / "test.txt"
        txt_file.write_text("Not an HWP file")
        
        with open(txt_file, "rb") as f:
            response = client.post(
                "/api/upload",
                files={"file": ("test.txt", f, "text/plain")}
            )
        
        assert response.status_code == 400
        assert "Invalid file type" in response.json()["detail"]
    
    def test_upload_creates_job_directory(self, client, sample_hwp_file):
        """Test that upload creates job directory with source file"""
        with open(sample_hwp_file, "rb") as f:
            response = client.post(
                "/api/upload",
                files={"file": ("test.hwp", f, "application/octet-stream")}
            )
        
        job_id = response.json()["job_id"]
        job = job_queue.get_job(job_id)
        
        assert job is not None
        assert Path(job.source_path).exists()


class TestStatusEndpoint:
    """Tests for GET /api/status/{job_id}"""
    
    def test_get_status_pending(self, client, sample_hwp_file):
        """Test status check for pending job"""
        # First upload a file
        with open(sample_hwp_file, "rb") as f:
            upload_response = client.post(
                "/api/upload",
                files={"file": ("test.hwp", f, "application/octet-stream")}
            )
        job_id = upload_response.json()["job_id"]
        
        # Check status
        response = client.get(f"/api/status/{job_id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["job_id"] == job_id
        assert data["status"] == "pending"
        assert data["source_filename"] == "test.hwp"
    
    def test_get_status_not_found(self, client):
        """Test status check for non-existent job"""
        response = client.get("/api/status/nonexistent-job-id")
        assert response.status_code == 404


class TestDownloadEndpoint:
    """Tests for GET /api/download/{job_id}"""
    
    def test_download_pending_returns_202(self, client, sample_hwp_file):
        """Test download for pending job returns 202"""
        with open(sample_hwp_file, "rb") as f:
            upload_response = client.post(
                "/api/upload",
                files={"file": ("test.hwp", f, "application/octet-stream")}
            )
        job_id = upload_response.json()["job_id"]
        
        response = client.get(f"/api/download/{job_id}")
        assert response.status_code == 202
    
    def test_download_not_found(self, client):
        """Test download for non-existent job"""
        response = client.get("/api/download/nonexistent-job-id")
        assert response.status_code == 404


class TestHealthEndpoint:
    """Tests for health check"""
    
    def test_health_check(self, client):
        """Test health endpoint returns healthy"""
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"
