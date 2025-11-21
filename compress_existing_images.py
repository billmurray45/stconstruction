"""
Script to compress all existing uploaded images
Run once to optimize all images that were uploaded before compression was implemented
"""
import logging
from pathlib import Path
from PIL import Image
import shutil
import sys

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(message)s'
)
logger = logging.getLogger(__name__)


def compress_image(
    image_path: Path,
    max_width: int = 1920,
    max_height: int = 1080,
    quality: int = 85,
    backup: bool = True
) -> bool:
    """
    Compress a single image file

    Args:
        image_path: Path to image file
        max_width: Maximum width in pixels
        max_height: Maximum height in pixels
        quality: JPEG quality 1-100
        backup: Create backup before compression

    Returns:
        True if compressed successfully, False otherwise
    """
    try:
        # Skip if not an image file
        if image_path.suffix.lower() not in ['.jpg', '.jpeg', '.png', '.webp', '.gif']:
            logger.debug(f"Skipping non-image file: {image_path.name}")
            return False

        # Skip SVG files
        if image_path.suffix.lower() == '.svg':
            logger.info(f"Skipping SVG (no compression needed): {image_path.name}")
            return False

        # Get original size
        original_size = image_path.stat().st_size
        original_size_mb = original_size / (1024 * 1024)

        # Skip if already small (< 100KB)
        if original_size < 100 * 1024:
            logger.info(f"Skipping small file ({original_size_mb:.2f}MB): {image_path.name}")
            return False

        # Create backup if requested
        if backup:
            backup_path = image_path.with_suffix(image_path.suffix + '.backup')
            if not backup_path.exists():
                shutil.copy2(image_path, backup_path)
                logger.debug(f"Created backup: {backup_path.name}")

        # Open image
        image = Image.open(image_path)

        # Get original dimensions
        original_width, original_height = image.size

        # Convert RGBA to RGB if saving as JPEG
        file_extension = image_path.suffix.lower()
        if image.mode in ('RGBA', 'LA', 'P') and file_extension in ['.jpg', '.jpeg']:
            # Create white background
            background = Image.new('RGB', image.size, (255, 255, 255))
            if image.mode == 'P':
                image = image.convert('RGBA')
            background.paste(image, mask=image.split()[-1] if image.mode == 'RGBA' else None)
            image = background
        elif image.mode != 'RGB' and file_extension in ['.jpg', '.jpeg']:
            image = image.convert('RGB')

        # Calculate new dimensions maintaining aspect ratio
        new_width, new_height = original_width, original_height
        if original_width > max_width or original_height > max_height:
            ratio = min(max_width / original_width, max_height / original_height)
            new_width = int(original_width * ratio)
            new_height = int(original_height * ratio)

            # Resize with high-quality resampling
            image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
            logger.debug(f"Resized: {original_width}x{original_height} -> {new_width}x{new_height}")

        # Prepare save options
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
            save_kwargs = {'format': image.format or 'PNG'}

        # Save compressed image
        image.save(image_path, **save_kwargs)

        # Get new size
        new_size = image_path.stat().st_size
        new_size_mb = new_size / (1024 * 1024)
        saved_percent = (1 - new_size / original_size) * 100

        logger.info(
            f"✓ Compressed: {image_path.name} | "
            f"{original_size_mb:.2f}MB -> {new_size_mb:.2f}MB | "
            f"Saved {saved_percent:.1f}%"
        )

        return True

    except Exception as e:
        logger.error(f"✗ Failed to compress {image_path.name}: {str(e)}")
        return False


def compress_directory(
    directory: Path,
    max_width: int = 1920,
    max_height: int = 1080,
    quality: int = 85,
    backup: bool = True,
    recursive: bool = True
) -> tuple[int, int]:
    """
    Compress all images in a directory

    Args:
        directory: Path to directory
        max_width: Maximum width in pixels
        max_height: Maximum height in pixels
        quality: JPEG quality 1-100
        backup: Create backups before compression
        recursive: Process subdirectories

    Returns:
        Tuple of (successful_count, failed_count)
    """
    if not directory.exists():
        logger.warning(f"Directory does not exist: {directory}")
        return 0, 0

    logger.info(f"\n{'='*60}")
    logger.info(f"Processing directory: {directory}")
    logger.info(f"{'='*60}")

    # Find all image files
    if recursive:
        image_files = [
            f for f in directory.rglob('*')
            if f.is_file() and f.suffix.lower() in ['.jpg', '.jpeg', '.png', '.webp', '.gif']
        ]
    else:
        image_files = [
            f for f in directory.glob('*')
            if f.is_file() and f.suffix.lower() in ['.jpg', '.jpeg', '.png', '.webp', '.gif']
        ]

    if not image_files:
        logger.info("No images found in directory")
        return 0, 0

    logger.info(f"Found {len(image_files)} image files")

    success_count = 0
    failed_count = 0

    for image_file in image_files:
        # Skip backup files
        if image_file.suffix == '.backup':
            continue

        if compress_image(image_file, max_width, max_height, quality, backup):
            success_count += 1
        else:
            failed_count += 1

    logger.info(f"\nDirectory summary: {success_count} compressed, {failed_count} skipped/failed")

    return success_count, failed_count


def main():
    """Main function to compress all uploaded images"""
    logger.info("="*60)
    logger.info("Starting image compression for existing uploads")
    logger.info("="*60)

    base_path = Path("app/static/uploads")

    if not base_path.exists():
        logger.error(f"Upload directory does not exist: {base_path}")
        sys.exit(1)

    # Directories to process
    directories = [
        (base_path / "news", 1920, 1080, 85),      # News images
        (base_path / "projects", 1920, 1080, 85),  # Project images
        (base_path / "settings", 800, 800, 90),    # Logo (smaller, higher quality)
    ]

    total_success = 0
    total_failed = 0

    for directory, max_w, max_h, qual in directories:
        success, failed = compress_directory(
            directory,
            max_width=max_w,
            max_height=max_h,
            quality=qual,
            backup=True,
            recursive=True
        )
        total_success += success
        total_failed += failed

    # Final summary
    logger.info("\n" + "="*60)
    logger.info("COMPRESSION COMPLETE")
    logger.info("="*60)
    logger.info(f"Total images compressed: {total_success}")
    logger.info(f"Total images skipped/failed: {total_failed}")
    logger.info("\nBackup files created with .backup extension")
    logger.info("If everything looks good, you can delete backup files with:")
    logger.info("  find app/static/uploads -name '*.backup' -delete")
    logger.info("="*60)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("\n\nCompression cancelled by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"\n\nUnexpected error: {str(e)}")
        sys.exit(1)
