"""
File Handling Schemas
"""
from datetime import datetime
from typing import List

from pydantic import BaseModel, Field


class FileUploadResponse(BaseModel):
    """Response after successful file upload"""
    id: str = Field(..., description="Unique file identifier")
    filename: str = Field(..., description="Original filename")
    content_type: str = Field(..., description="MIME type of the file")
    size: int = Field(..., description="File size in bytes")
    url: str = Field(..., description="URL to download the file")
    uploaded_at: datetime = Field(default_factory=datetime.utcnow)


class FileInfo(BaseModel):
    """File information"""
    id: str
    filename: str
    content_type: str
    size: int
    uploaded_by: str
    uploaded_at: datetime
    url: str


class FileListResponse(BaseModel):
    """Response for listing files"""
    files: List[FileInfo]
    total: int
