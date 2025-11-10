"""
File Upload Validation Utilities
Provides secure file upload validation for images
"""
from fastapi import UploadFile, HTTPException
from pathlib import Path
from typing import List, Optional
import imghdr
import os


ALLOWED_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp", ".svg"}
ALLOWED_IMAGE_MIMES = {
    "image/jpeg",
    "image/png",
    "image/gif",
    "image/webp",
    "image/svg+xml"
}


MAX_IMAGE_SIZE = 10 * 1024 * 1024  # 10 MB
MAX_LOGO_SIZE = 5 * 1024 * 1024    # 5 MB


class FileValidationError(HTTPException):
    """Custom exception for file validation errors"""
    def __init__(self, detail: str):
        super().__init__(status_code=400, detail=detail)


async def validate_image_upload(
    file: UploadFile,
    max_size: int = MAX_IMAGE_SIZE,
    allowed_extensions: Optional[set] = None,
    field_name: str = "файл"
) -> None:
    """
    Validates uploaded image file

    Args:
        file: FastAPI UploadFile object
        max_size: Maximum allowed file size in bytes
        allowed_extensions: Set of allowed file extensions (with dot)
        field_name: Name of field for error messages (Russian)

    Raises:
        FileValidationError: If validation fails
    """
    if allowed_extensions is None:
        allowed_extensions = ALLOWED_IMAGE_EXTENSIONS

    # 1. Check if file is provided
    if not file or not file.filename:
        raise FileValidationError(f"Необходимо загрузить {field_name}")

    # 2. Validate file extension
    file_extension = Path(file.filename).suffix.lower()
    if file_extension not in allowed_extensions:
        allowed_list = ", ".join(allowed_extensions)
        raise FileValidationError(
            f"Недопустимый формат файла. Разрешены: {allowed_list}"
        )

    # 3. Validate MIME type
    if file.content_type not in ALLOWED_IMAGE_MIMES:
        raise FileValidationError(
            f"Недопустимый тип файла: {file.content_type}. "
            f"Ожидается изображение."
        )

    # 4. Validate file size
    # Read file content to check size
    file_content = await file.read()
    file_size = len(file_content)

    if file_size == 0:
        raise FileValidationError(f"Загруженный {field_name} пуст")

    if file_size > max_size:
        max_size_mb = max_size / (1024 * 1024)
        raise FileValidationError(
            f"Размер файла превышает {max_size_mb:.1f} МБ"
        )

    # 5. Validate image format (magic bytes)
    # Reset file pointer for imghdr
    try:
        # imghdr.what() reads from file-like object
        # We need to validate actual image format
        image_type = imghdr.what(None, h=file_content)

        # For SVG (imghdr doesn't detect it)
        if file_extension == ".svg":
            # Basic SVG validation - check if starts with XML/SVG tags
            if not (file_content.startswith(b'<?xml') or
                    file_content.startswith(b'<svg') or
                    b'<svg' in file_content[:200]):
                raise FileValidationError("Недействительный SVG файл")
        elif image_type is None:
            raise FileValidationError(
                "Файл не является изображением или поврежден"
            )
        elif image_type not in ['jpeg', 'png', 'gif', 'webp']:
            raise FileValidationError(
                f"Неподдерживаемый формат изображения: {image_type}"
            )
    except Exception as e:
        if isinstance(e, FileValidationError):
            raise
        raise FileValidationError("Ошибка при проверке формата изображения")

    # 6. Reset file pointer for subsequent use
    await file.seek(0)


async def validate_multiple_images(
    files: List[UploadFile],
    max_files: int = 10,
    max_size_per_file: int = MAX_IMAGE_SIZE,
    field_name: str = "изображения"
) -> None:
    """
    Validates multiple uploaded images

    Args:
        files: List of FastAPI UploadFile objects
        max_files: Maximum number of files allowed
        max_size_per_file: Maximum size per file in bytes
        field_name: Name of field for error messages (Russian)

    Raises:
        FileValidationError: If validation fails
    """
    # Check if any files provided
    if not files or (len(files) == 1 and not files[0].filename):
        return  # No files to validate (optional upload)

    # Check max number of files
    valid_files = [f for f in files if f.filename]
    if len(valid_files) > max_files:
        raise FileValidationError(
            f"Можно загрузить максимум {max_files} {field_name}"
        )

    # Validate each file
    for i, file in enumerate(valid_files, 1):
        try:
            await validate_image_upload(
                file,
                max_size=max_size_per_file,
                field_name=f"{field_name} #{i}"
            )
        except FileValidationError as e:
            # Re-raise with file number
            raise FileValidationError(f"{field_name} #{i}: {e.detail}")


def sanitize_filename(filename: str) -> str:
    """
    Sanitizes filename to prevent path traversal and other attacks

    Args:
        filename: Original filename

    Returns:
        Sanitized filename (only alphanumeric, dash, underscore, dot)
    """
    # Get extension
    path = Path(filename)
    extension = path.suffix.lower()
    name = path.stem

    # Remove any non-alphanumeric characters (except dash and underscore)
    safe_name = "".join(
        c for c in name if c.isalnum() or c in ('-', '_')
    )

    # If name becomes empty, use 'file'
    if not safe_name:
        safe_name = "file"

    # Limit length
    safe_name = safe_name[:100]

    return f"{safe_name}{extension}"


async def save_uploaded_file(
    file: UploadFile,
    destination_dir: Path,
    unique_filename: str
) -> Path:
    """
    Safely saves uploaded file to disk

    Args:
        file: FastAPI UploadFile object (already validated)
        destination_dir: Directory to save file
        unique_filename: Unique filename to use

    Returns:
        Path to saved file

    Raises:
        Exception: If save fails
    """
    # Ensure directory exists
    destination_dir.mkdir(parents=True, exist_ok=True)

    file_path = destination_dir / unique_filename

    # Write file
    try:
        with open(file_path, "wb") as buffer:
            # File pointer should be at start (from validate_image_upload)
            content = await file.read()
            buffer.write(content)

        return file_path
    except Exception as e:
        # Clean up partial file if exists
        if file_path.exists():
            os.remove(file_path)
        raise Exception(f"Ошибка при сохранении файла: {str(e)}")
