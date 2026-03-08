"""
File Service

Handles file upload, download, and management.
"""
import logging
import os
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional, AsyncGenerator

import aiofiles
from fastapi import UploadFile, HTTPException, status

logger = logging.getLogger("bookapi.files")

# Configuration
UPLOAD_DIR = Path("uploads")
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
ALLOWED_EXTENSIONS = {
    "image": [".jpg", ".jpeg", ".png", ".gif", ".webp"],
    "document": [".pdf", ".doc", ".docx", ".txt", ".md"],
    "book_cover": [".jpg", ".jpeg", ".png", ".webp"],
}
ALLOWED_CONTENT_TYPES = {
    "image/jpeg", "image/png", "image/gif", "image/webp",
    "application/pdf", "text/plain", "text/markdown",
    "application/msword",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
}


class FileService:
    """Service for handling file operations."""

    def __init__(self):
        # Ensure upload directory exists
        UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def _generate_file_id() -> str:
        """Generate a unique file ID."""
        return str(uuid.uuid4())

    @staticmethod
    def _get_file_extension(filename: str) -> str:
        """Get file extension from filename."""
        return Path(filename).suffix.lower()

    @staticmethod
    def _validate_file_type(filename: str, content_type: str, category: str = "image") -> bool:
        """Validate file type against allowed types."""
        ext = Path(filename).suffix.lower()
        allowed_exts = ALLOWED_EXTENSIONS.get(category, [])

        if ext not in allowed_exts:
            return False

        if content_type not in ALLOWED_CONTENT_TYPES:
            return False

        return True

    @staticmethod
    def _get_user_upload_dir(user_id: str) -> Path:
        """Get or create user-specific upload directory."""
        user_dir = UPLOAD_DIR / user_id
        user_dir.mkdir(parents=True, exist_ok=True)
        return user_dir

    async def save_file(
            self,
            file: UploadFile,
            user_id: str,
            category: str = "image"
    ) -> dict:
        """
        Save an uploaded file.

        Args:
            file: The uploaded file
            user_id: ID of the user uploading the file
            category: File category for validation

        Returns:
            dict with file information
        """
        # Validate file type
        if not self._validate_file_type(file.filename, file.content_type, category):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid file type. Allowed types for {category}: {ALLOWED_EXTENSIONS.get(category, [])}"
            )

        # Read file to check size
        content = await file.read()
        file_size = len(content)

        if file_size > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"File too large. Maximum size: {MAX_FILE_SIZE // (1024 * 1024)}MB"
            )

        # Generate unique filename
        file_id = self._generate_file_id()
        ext = self._get_file_extension(file.filename)
        new_filename = f"{file_id}{ext}"

        # Get user upload directory
        user_dir = self._get_user_upload_dir(user_id)
        file_path = user_dir / new_filename

        # Save file
        async with aiofiles.open(file_path, "wb") as f:
            await f.write(content)

        logger.info(f"File saved: {file_path} ({file_size} bytes)")

        return {
            "id": file_id,
            "filename": file.filename,
            "stored_filename": new_filename,
            "content_type": file.content_type,
            "size": file_size,
            "path": str(file_path),
            "url": f"/api/v1/files/{user_id}/{new_filename}",
            "uploaded_at": datetime.utcnow()
        }

    async def get_file_path(self, user_id: str, filename: str) -> Optional[Path]:
        """Get the path to a stored file."""
        file_path = UPLOAD_DIR / user_id / filename

        if not file_path.exists():
            return None

        return file_path

    async def delete_file(self, user_id: str, filename: str) -> bool:
        """Delete a file."""
        file_path = UPLOAD_DIR / user_id / filename

        if not file_path.exists():
            return False

        try:
            os.remove(file_path)
            logger.info(f"File deleted: {file_path}")
            return True
        except Exception as e:
            logger.error(f"Error deleting file {file_path}: {e}")
            return False

    async def stream_file(self, file_path: Path, chunk_size: int = 8192) -> AsyncGenerator[bytes, None]:
        """
        Stream a file in chunks.

        Args:
            file_path: Path to the file
            chunk_size: Size of each chunk in bytes

        Yields:
            File content in chunks
        """
        async with aiofiles.open(file_path, "rb") as f:
            while True:
                chunk = await f.read(chunk_size)
                if not chunk:
                    break
                yield chunk

    def get_user_files(self, user_id: str) -> list:
        """Get list of files uploaded by a user."""
        user_dir = UPLOAD_DIR / user_id

        if not user_dir.exists():
            return []

        files = []
        for file_path in user_dir.iterdir():
            if file_path.is_file():
                stat = file_path.stat()
                files.append({
                    "filename": file_path.name,
                    "size": stat.st_size,
                    "uploaded_at": datetime.fromtimestamp(stat.st_mtime),
                    "url": f"/api/v1/files/{user_id}/{file_path.name}"
                })

        return files


# Global file service instance
file_service = FileService()
