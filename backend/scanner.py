"""
File scanner for recursively scanning directories and extracting file information
"""
import logging
import asyncio
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, List
import magic
from PIL import Image
import cv2
import imagehash
from config import (
    SUPPORTED_EXTENSIONS,
    IMAGE_EXTENSIONS,
    VIDEO_EXTENSIONS,
    MAX_FILE_SIZE_MB,
    HASH_SIZE,
    VIDEO_FRAME_POSITION
)
from database import db

logger = logging.getLogger(__name__)


class ScanStatus:
    """Thread-safe scan status tracker"""
    def __init__(self):
        self.is_scanning = False
        self.scanned_path: Optional[str] = None
        self.file_type: str = 'both'
        self.total_files = 0
        self.processed_files = 0
        self.current_file: Optional[str] = None
        self.errors: List[str] = []
        self.start_time: Optional[datetime] = None
        self.end_time: Optional[datetime] = None

    def reset(self):
        """Reset status for new scan"""
        self.is_scanning = False
        self.scanned_path = None
        self.file_type = 'both'
        self.total_files = 0
        self.processed_files = 0
        self.current_file = None
        self.errors = []
        self.start_time = None
        self.end_time = None

    def to_dict(self) -> Dict:
        """Convert to dictionary for API response"""
        return {
            'is_scanning': self.is_scanning,
            'scanned_path': self.scanned_path,
            'file_type': self.file_type,
            'total_files': self.total_files,
            'processed_files': self.processed_files,
            'current_file': self.current_file,
            'errors': self.errors,
            'start_time': self.start_time,
            'end_time': self.end_time
        }


# Global scan status
scan_status = ScanStatus()


class FileScanner:
    """Scanner for finding and processing image/video files"""

    @staticmethod
    def find_files(directory: Path, file_type: str = 'both') -> List[Path]:
        """Recursively find all supported files in directory

        Args:
            directory: Path to scan
            file_type: 'image', 'video', or 'both'
        """
        files = []

        # Determine which extensions to look for
        if file_type == 'image':
            allowed_extensions = IMAGE_EXTENSIONS
        elif file_type == 'video':
            allowed_extensions = VIDEO_EXTENSIONS
        else:  # both
            allowed_extensions = SUPPORTED_EXTENSIONS

        try:
            for item in directory.rglob('*'):
                if item.is_file() and item.suffix.lower() in allowed_extensions:
                    # Check file size
                    size_mb = item.stat().st_size / (1024 * 1024)
                    if size_mb <= MAX_FILE_SIZE_MB:
                        files.append(item)
                    else:
                        logger.warning(f"Skipping large file ({size_mb:.2f}MB): {item}")
        except PermissionError as e:
            logger.error(f"Permission denied accessing {directory}: {e}")
        except Exception as e:
            logger.error(f"Error scanning directory {directory}: {e}")

        return files

    @staticmethod
    def get_file_type(file_path: Path) -> Optional[str]:
        """Determine if file is image or video"""
        ext = file_path.suffix.lower()
        if ext in IMAGE_EXTENSIONS:
            return 'image'
        elif ext in VIDEO_EXTENSIONS:
            return 'video'
        return None

    @staticmethod
    def extract_image_info(file_path: Path) -> Optional[Dict]:
        """Extract dimensions and hash from image"""
        try:
            with Image.open(file_path) as img:
                width, height = img.size

                # Compute perceptual hash
                phash = imagehash.phash(img, hash_size=HASH_SIZE)

                return {
                    'width': width,
                    'height': height,
                    'hash': str(phash)
                }
        except Exception as e:
            logger.error(f"Error processing image {file_path}: {e}")
            return None

    @staticmethod
    def extract_video_info(file_path: Path) -> Optional[Dict]:
        """Extract dimensions and representative frame hash from video"""
        try:
            cap = cv2.VideoCapture(str(file_path))

            if not cap.isOpened():
                logger.error(f"Cannot open video: {file_path}")
                return None

            # Get video properties
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

            # Extract frame at VIDEO_FRAME_POSITION
            frame_number = int(frame_count * VIDEO_FRAME_POSITION)
            cap.set(cv2.CAP_PROP_POS_FRAMES, frame_number)

            ret, frame = cap.read()
            cap.release()

            if not ret:
                logger.error(f"Cannot extract frame from video: {file_path}")
                return None

            # Convert BGR to RGB
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            img = Image.fromarray(frame_rgb)

            # Compute perceptual hash
            phash = imagehash.phash(img, hash_size=HASH_SIZE)

            return {
                'width': width,
                'height': height,
                'hash': str(phash)
            }
        except Exception as e:
            logger.error(f"Error processing video {file_path}: {e}")
            return None

    @staticmethod
    async def process_file(file_path: Path) -> Optional[Dict]:
        """Process a single file and extract all information"""
        try:
            stat = file_path.stat()
            file_type = FileScanner.get_file_type(file_path)

            if not file_type:
                return None

            # Basic file info
            file_data = {
                'path': str(file_path.resolve()),
                'filename': file_path.name,
                'size_bytes': stat.st_size,
                'created_at': datetime.fromtimestamp(stat.st_ctime),
                'modified_at': datetime.fromtimestamp(stat.st_mtime),
                'file_type': file_type
            }

            # Check if already cached with same modified time
            cached = await db.get_file_by_path(file_data['path'])
            if cached and datetime.fromisoformat(cached['modified_at']) == file_data['modified_at']:
                logger.debug(f"Using cached data for {file_path.name}")
                return cached

            # Extract type-specific information
            if file_type == 'image':
                info = FileScanner.extract_image_info(file_path)
            elif file_type == 'video':
                info = FileScanner.extract_video_info(file_path)
            else:
                info = None

            if info:
                file_data.update(info)
            else:
                # If extraction failed, still store basic info
                logger.warning(f"Could not extract detailed info from {file_path}")

            # Save to database
            await db.insert_or_update_file(file_data)

            return file_data

        except Exception as e:
            logger.error(f"Error processing file {file_path}: {e}")
            scan_status.errors.append(f"{file_path.name}: {str(e)}")
            return None

    @staticmethod
    async def scan_directory(directory: str, file_type: str = 'both', clear_cache: bool = True) -> Dict:
        """Scan directory recursively and process all files

        Args:
            directory: Directory path to scan
            file_type: 'image', 'video', or 'both'
            clear_cache: Clear database cache before scanning
        """
        global scan_status

        if scan_status.is_scanning:
            raise RuntimeError("A scan is already in progress")

        scan_status.reset()
        scan_status.is_scanning = True
        scan_status.scanned_path = directory
        scan_status.file_type = file_type
        scan_status.start_time = datetime.now()

        try:
            dir_path = Path(directory)
            logger.info(f"Starting scan of {directory} (file_type: {file_type}, clear_cache: {clear_cache})")

            # Clear cache if requested
            if clear_cache:
                logger.info("Clearing database cache before scan")
                await db.clear_all()

            # Find all files
            files = FileScanner.find_files(dir_path, file_type)
            scan_status.total_files = len(files)
            logger.info(f"Found {len(files)} files to process")

            # Process files
            for file_path in files:
                scan_status.current_file = file_path.name
                await FileScanner.process_file(file_path)
                scan_status.processed_files += 1

            scan_status.end_time = datetime.now()
            scan_status.is_scanning = False

            duration = (scan_status.end_time - scan_status.start_time).total_seconds()
            logger.info(f"Scan completed in {duration:.2f} seconds")

            return scan_status.to_dict()

        except Exception as e:
            logger.error(f"Error during scan: {e}")
            scan_status.errors.append(str(e))
            scan_status.end_time = datetime.now()
            scan_status.is_scanning = False
            raise
