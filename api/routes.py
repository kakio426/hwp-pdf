"""API routes for HWP to PDF conversion"""
import os
import shutil
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import FileResponse

from .models import JobResponse, JobDetailResponse, JobStatus
from .queue import job_queue

router = APIRouter()

# Storage configuration
STORAGE_DIR = Path(__file__).parent.parent / "storage"
STORAGE_DIR.mkdir(exist_ok=True)


def get_job_dir(job_id: str) -> Path:
    """Get the directory for a specific job"""
    return STORAGE_DIR / job_id


@router.post("/upload", response_model=JobResponse)
async def upload_hwp(file: UploadFile = File(...)):
    """
    Upload an HWP file for PDF conversion.
    
    Returns a job ID that can be used to check status and download the result.
    """
    # Validate file extension
    if not file.filename:
        raise HTTPException(status_code=400, detail="Filename is required")
    
    ext = Path(file.filename).suffix.lower()
    if ext not in ('.hwp', '.hwpx', '.odt', '.docx'):
        raise HTTPException(
            status_code=400, 
            detail=f"Invalid file type: {ext}. Only .hwp, .hwpx, .odt, .docx files are accepted."
        )
    
    # Create job first to get ID
    job = job_queue.add_job(
        source_filename=file.filename,
        source_path=""  # Will be set after saving
    )
    
    # Create job directory and save file
    job_dir = get_job_dir(job.job_id)
    job_dir.mkdir(parents=True, exist_ok=True)
    
    source_path = job_dir / f"source{ext}"
    
    try:
        with open(source_path, "wb") as f:
            shutil.copyfileobj(file.file, f)
    except Exception as e:
        job_queue.update_status(job.job_id, JobStatus.FAILED, error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to save file: {e}")
    
    # Update job with actual path
    job.source_path = str(source_path)
    
    return JobResponse(
        job_id=job.job_id,
        status=job.status,
        created_at=job.created_at,
        message=f"File '{file.filename}' uploaded successfully. Conversion pending."
    )


@router.get("/status/{job_id}", response_model=JobDetailResponse)
async def get_job_status(job_id: str):
    """Get the status of a conversion job"""
    job = job_queue.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Job not found: {job_id}")
    
    return JobDetailResponse(
        job_id=job.job_id,
        status=job.status,
        created_at=job.created_at,
        source_filename=job.source_filename,
        output_path=job.output_path,
        error=job.error,
        completed_at=job.completed_at,
    )


@router.get("/download/{job_id}")
async def download_pdf(job_id: str):
    """Download the converted PDF file"""
    job = job_queue.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Job not found: {job_id}")
    
    if job.status == JobStatus.PENDING:
        raise HTTPException(status_code=202, detail="Conversion is still pending")
    
    if job.status == JobStatus.PROCESSING:
        raise HTTPException(status_code=202, detail="Conversion is in progress")
    
    if job.status == JobStatus.FAILED:
        raise HTTPException(status_code=500, detail=f"Conversion failed: {job.error}")
    
    if not job.output_path or not Path(job.output_path).exists():
        raise HTTPException(status_code=500, detail="Output file not found")
    
    # Generate download filename from original
    download_name = Path(job.source_filename).stem + ".pdf"
    
    return FileResponse(
        path=job.output_path,
        filename=download_name,
        media_type="application/pdf"
    )


@router.get("/jobs")
async def list_jobs():
    """List all jobs (for debugging)"""
    jobs = job_queue.get_all_jobs()
    return [
        {
            "job_id": j.job_id,
            "status": j.status,
            "source_filename": j.source_filename,
            "created_at": j.created_at.isoformat(),
        }
        for j in jobs
    ]
