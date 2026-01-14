"""Pydantic models for API"""
from datetime import datetime
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


class JobStatus(str, Enum):
    """Job processing status"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class JobResponse(BaseModel):
    """Response for job creation and status check"""
    job_id: str
    status: JobStatus
    created_at: datetime
    message: Optional[str] = None


class JobDetailResponse(JobResponse):
    """Detailed job response including file info"""
    source_filename: str
    output_path: Optional[str] = None
    error: Optional[str] = None
    completed_at: Optional[datetime] = None
