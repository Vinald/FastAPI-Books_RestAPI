"""
File Handling Routes

Upload, download, and manage files.
"""
import mimetypes
from typing import List

from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, status, BackgroundTasks, Query, Request
from fastapi.responses import StreamingResponse, FileResponse

from app.core.rate_limit import limiter
from app.core.security import get_current_active_user
from app.core.tasks.tasks import process_file_task
from app.models.user import User
from app.schemas.auth import MessageResponse
from app.schemas.file import FileUploadResponse, FileInfo, FileListResponse
from app.services.file_service import file_service

file_router = APIRouter(
    prefix="/files",
    tags=["Files"],
)


@file_router.post(
    "/upload",
    response_model=FileUploadResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload a file",
    description="Upload a file (images, documents). Maximum size: 10MB."
)
@limiter.limit("10/minute")
async def upload_file(
        request: Request,
        file: UploadFile = File(..., description="File to upload"),
        category: str = Query(default="image", description="File category: image, document, book_cover"),
        background_tasks: BackgroundTasks = None,
        current_user: User = Depends(get_current_active_user)
) -> FileUploadResponse:
    """Upload a file."""
    result = await file_service.save_file(
        file=file,
        user_id=str(current_user.uuid),
        category=category
    )

    # Optionally process file in background
    if background_tasks:
        background_tasks.add_task(
            lambda: process_file_task.delay(
                result["path"],
                "process",
                current_user.id
            )
        )

    return FileUploadResponse(
        id=result["id"],
        filename=result["filename"],
        content_type=result["content_type"],
        size=result["size"],
        url=result["url"],
        uploaded_at=result["uploaded_at"]
    )


@file_router.post(
    "/upload/multiple",
    response_model=List[FileUploadResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Upload multiple files",
    description="Upload multiple files at once. Maximum 5 files, 10MB each."
)
@limiter.limit("5/minute")
async def upload_multiple_files(
        request: Request,
        files: List[UploadFile] = File(..., description="Files to upload (max 5)"),
        category: str = Query(default="image", description="File category"),
        current_user: User = Depends(get_current_active_user)
) -> List[FileUploadResponse]:
    """Upload multiple files."""
    if len(files) > 5:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Maximum 5 files allowed per request"
        )

    results = []
    for file in files:
        result = await file_service.save_file(
            file=file,
            user_id=str(current_user.uuid),
            category=category
        )
        results.append(FileUploadResponse(
            id=result["id"],
            filename=result["filename"],
            content_type=result["content_type"],
            size=result["size"],
            url=result["url"],
            uploaded_at=result["uploaded_at"]
        ))

    return results


@file_router.get(
    "/my-files",
    response_model=FileListResponse,
    summary="List my uploaded files",
    description="Get a list of all files uploaded by the current user."
)
async def list_my_files(
        current_user: User = Depends(get_current_active_user)
) -> FileListResponse:
    """Get list of user's uploaded files."""
    files = file_service.get_user_files(str(current_user.uuid))

    return FileListResponse(
        files=[
            FileInfo(
                id=f["filename"].split(".")[0],
                filename=f["filename"],
                content_type=mimetypes.guess_type(f["filename"])[0] or "application/octet-stream",
                size=f["size"],
                uploaded_by=str(current_user.uuid),
                uploaded_at=f["uploaded_at"],
                url=f["url"]
            )
            for f in files
        ],
        total=len(files)
    )


@file_router.get(
    "/{user_id}/{filename}",
    summary="Download a file",
    description="Download a file by user ID and filename."
)
async def download_file(
        user_id: str,
        filename: str
):
    """Download a file."""
    file_path = await file_service.get_file_path(user_id, filename)

    if not file_path:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found"
        )

    # Get content type
    content_type = mimetypes.guess_type(filename)[0] or "application/octet-stream"

    return FileResponse(
        path=file_path,
        filename=filename,
        media_type=content_type
    )


@file_router.get(
    "/{user_id}/{filename}/stream",
    summary="Stream a file",
    description="Stream a file for large file downloads."
)
async def stream_file(
        user_id: str,
        filename: str
):
    """Stream a file."""
    file_path = await file_service.get_file_path(user_id, filename)

    if not file_path:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found"
        )

    # Get content type and file size
    content_type = mimetypes.guess_type(filename)[0] or "application/octet-stream"
    file_size = file_path.stat().st_size

    return StreamingResponse(
        file_service.stream_file(file_path),
        media_type=content_type,
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "Content-Length": str(file_size)
        }
    )


@file_router.delete(
    "/{filename}",
    response_model=MessageResponse,
    summary="Delete a file",
    description="Delete an uploaded file. Users can only delete their own files."
)
async def delete_file(
        filename: str,
        current_user: User = Depends(get_current_active_user)
) -> MessageResponse:
    """Delete a file."""
    success = await file_service.delete_file(str(current_user.uuid), filename)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found or could not be deleted"
        )

    return MessageResponse(message=f"File {filename} deleted successfully")
