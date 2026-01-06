"""
Pydantic models for request/response validation
"""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, field_validator
from pathlib import Path


class ScanRequest(BaseModel):
    """Request to start scanning a directory"""
    path: str = Field(..., description="Directory path to scan")
    similarity_threshold: int = Field(
        default=5,
        ge=0,
        le=15,
        description="Hamming distance threshold (0=identical, 15=very different)"
    )
    file_type: str = Field(
        default='both',
        description="Type of files to scan: 'image', 'video', or 'both'"
    )

    @field_validator('path')
    @classmethod
    def validate_path(cls, v):
        p = Path(v)
        if not p.exists():
            raise ValueError(f"Path does not exist: {v}")
        if not p.is_dir():
            raise ValueError(f"Path is not a directory: {v}")
        return str(p.resolve())

    @field_validator('file_type')
    @classmethod
    def validate_file_type(cls, v):
        if v not in ['image', 'video', 'both']:
            raise ValueError("file_type must be 'image', 'video', or 'both'")
        return v


class FileInfo(BaseModel):
    """Information about a single file"""
    path: str
    filename: str
    size_mb: float
    width: Optional[int] = None
    height: Optional[int] = None
    created_at: datetime
    modified_at: datetime
    file_type: str  # 'image' or 'video'
    hash: Optional[str] = None


class DuplicatePair(BaseModel):
    """A pair of similar/duplicate files"""
    file1: FileInfo
    file2: FileInfo
    similarity_score: int  # Hamming distance (0 = identical)
    similarity_percentage: float  # 100% = identical


class ScanStatus(BaseModel):
    """Status of ongoing scan operation"""
    is_scanning: bool
    scanned_path: Optional[str] = None
    total_files: int = 0
    processed_files: int = 0
    current_file: Optional[str] = None
    errors: List[str] = []
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None


class DuplicatesResponse(BaseModel):
    """Response containing duplicate pairs"""
    pairs: List[DuplicatePair]
    total_pairs: int
    total_potential_savings_mb: float


class DeleteRequest(BaseModel):
    """Request to delete a file"""
    file_path: str
    scan_base_path: str  # For security validation

    @field_validator('file_path')
    @classmethod
    def validate_file_path(cls, v):
        p = Path(v)
        if not p.exists():
            raise ValueError(f"File does not exist: {v}")
        if not p.is_file():
            raise ValueError(f"Path is not a file: {v}")
        return str(p.resolve())


class DeleteResponse(BaseModel):
    """Response after deleting a file"""
    success: bool
    message: str
    deleted_path: Optional[str] = None


class StatsResponse(BaseModel):
    """General statistics"""
    total_files_cached: int
    total_images: int
    total_videos: int
    total_size_mb: float
    cache_created_at: Optional[datetime] = None
