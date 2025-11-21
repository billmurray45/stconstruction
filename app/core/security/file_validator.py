"""
File Upload Validation Utilities
Provides secure file upload validation for images
"""
import logging
from fastapi import UploadFile, HTTPException
from pathlib import Path
from typing import List, Optional
import imghdr
import os
from PIL import Image
import io

logger = logging.getLogger(__name__)


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
        logger.warning(
            f"File upload rejected - invalid extension: "
            f"filename={file.filename}, extension={file_extension}, "
            f"content_type={file.content_type}"
        )
        raise FileValidationError(
            f"Недопустимый формат файла. Разрешены: {allowed_list}"
        )

    # 3. Validate MIME type
    if file.content_type not in ALLOWED_IMAGE_MIMES:
        logger.warning(
            f"File upload rejected - invalid MIME type: "
            f"filename={file.filename}, content_type={file.content_type}"
        )
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
        file_size_mb = file_size / (1024 * 1024)
        logger.warning(
            f"File upload rejected - size too large: "
            f"filename={file.filename}, size={file_size_mb:.2f}MB, max={max_size_mb:.1f}MB"
        )
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
                logger.warning(
                    f"File upload rejected - invalid SVG: filename={file.filename}"
                )
                raise FileValidationError("Недействительный SVG файл")
        elif image_type is None:
            logger.warning(
                f"File upload rejected - not an image or corrupted: "
                f"filename={file.filename}, extension={file_extension}"
            )
            raise FileValidationError(
                "Файл не является изображением или поврежден"
            )
        elif image_type not in ['jpeg', 'png', 'gif', 'webp']:
            logger.warning(
                f"File upload rejected - unsupported format: "
                f"filename={file.filename}, detected_type={image_type}"
            )
            raise FileValidationError(
                f"Неподдерживаемый формат изображения: {image_type}"
            )
    except Exception as e:
        if isinstance(e, FileValidationError):
            raise
        raise FileValidationError("Ошибка при проверке формата изображения")

    # 6. Reset file pointer for subsequent use
    await file.seek(0)

    # Log successful validation
    file_size_mb = file_size / (1024 * 1024)
    logger.info(
        f"File upload validated successfully: "
        f"filename={file.filename}, size={file_size_mb:.2f}MB, type={file_extension}"
    )


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

        file_size_mb = len(content) / (1024 * 1024)
        logger.info(
            f"File saved successfully: "
            f"original={file.filename}, saved_as={unique_filename}, "
            f"size={file_size_mb:.2f}MB, path={file_path}"
        )

        return file_path
    except Exception as e:
        logger.error(
            f"Failed to save file: "
            f"filename={file.filename}, path={file_path}, error={str(e)}"
        )
        # Clean up partial file if exists
        if file_path.exists():
            os.remove(file_path)
        raise Exception(f"Ошибка при сохранении файла: {str(e)}")


async def compress_and_save_image(
    file: UploadFile,
    destination_dir: Path,
    unique_filename: str,
    max_width: int = 1920,
    max_height: int = 1080,
    quality: int = 85
) -> Path:
    """
    Compresses and saves uploaded image to disk

    Args:
        file: FastAPI UploadFile object (already validated)
        destination_dir: Directory to save file
        unique_filename: Unique filename to use
        max_width: Maximum width in pixels (default: 1920)
        max_height: Maximum height in pixels (default: 1080)
        quality: JPEG quality 1-100 (default: 85)

    Returns:
        Path to saved file

    Raises:
        Exception: If save/compression fails
    """
    # Ensure directory exists
    destination_dir.mkdir(parents=True, exist_ok=True)

    file_path = destination_dir / unique_filename

    try:
        # Read file content
        content = await file.read()
        original_size_mb = len(content) / (1024 * 1024)

        # Check file extension
        file_extension = Path(unique_filename).suffix.lower()

        # SVG files - save without compression
        if file_extension == ".svg":
            with open(file_path, "wb") as buffer:
                buffer.write(content)
            logger.info(f"SVG saved without compression: {unique_filename}")
            return file_path

        # Open image with Pillow
        image = Image.open(io.BytesIO(content))

        # Convert RGBA to RGB if saving as JPEG
        if image.mode in ('RGBA', 'LA', 'P') and file_extension in ['.jpg', '.jpeg']:
            # Create white background
            background = Image.new('RGB', image.size, (255, 255, 255))
            if image.mode == 'P':
                image = image.convert('RGBA')
            background.paste(image, mask=image.split()[-1] if image.mode == 'RGBA' else None)
            image = background
        elif image.mode != 'RGB' and file_extension in ['.jpg', '.jpeg']:
            image = image.convert('RGB')

        # Get original dimensions
        original_width, original_height = image.size

        # Calculate new dimensions maintaining aspect ratio
        if original_width > max_width or original_height > max_height:
            ratio = min(max_width / original_width, max_height / original_height)
            new_width = int(original_width * ratio)
            new_height = int(original_height * ratio)

            # Resize with high-quality resampling
            image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
            logger.info(
                f"Image resized: {original_width}x{original_height} -> {new_width}x{new_height}"
            )

        # Save with compression
        save_kwargs = {}
        if file_extension in ['.jpg', '.jpeg']:
            save_kwargs = {
                'format': 'JPEG',
                'quality': quality,
                'optimize': True,
                'progressive': True
            }
        elif file_extension == '.png':
            save_kwargs = {
                'format': 'PNG',
                'optimize': True,
                'compress_level': 6
            }
        elif file_extension == '.webp':
            save_kwargs = {
                'format': 'WEBP',
                'quality': quality,
                'method': 6
            }
        else:
            # For GIF and other formats
            save_kwargs = {'format': image.format or 'PNG'}

        # Save optimized image
        image.save(file_path, **save_kwargs)

        # Get compressed size
        compressed_size_mb = file_path.stat().st_size / (1024 * 1024)
        compression_ratio = (1 - compressed_size_mb / original_size_mb) * 100

        logger.info(
            f"Image compressed and saved: "
            f"original={file.filename}, saved_as={unique_filename}, "
            f"original_size={original_size_mb:.2f}MB, "
            f"compressed_size={compressed_size_mb:.2f}MB, "
            f"saved={compression_ratio:.1f}%, path={file_path}"
        )

        return file_path

    except Exception as e:
        logger.error(
            f"Failed to compress/save image: "
            f"filename={file.filename}, path={file_path}, error={str(e)}"
        )
        # Clean up partial file if exists
        if file_path.exists():
            os.remove(file_path)
        raise Exception(f"Ошибка при сжатии и сохранении изображения: {str(e)}")
