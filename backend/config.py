"""
Configuration file for image deduplicator backend
"""
import os
from pathlib import Path

# Base paths
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DB_PATH = DATA_DIR / "image_cache.db"

# Supported file formats
IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.tiff', '.tif'}
VIDEO_EXTENSIONS = {'.mp4', '.avi', '.mov', '.mkv', '.webm', '.flv', '.wmv'}
SUPPORTED_EXTENSIONS = IMAGE_EXTENSIONS | VIDEO_EXTENSIONS

# Hash algorithm configuration
HASH_SIZE = 8  # Size for perceptual hash (8x8 = 64 bits)

# Similarity thresholds
DEFAULT_SIMILARITY_THRESHOLD = 5  # Hamming distance (0 = identical, 10 = very different)
MAX_SIMILARITY_THRESHOLD = 15

# Scanning configuration
MAX_FILE_SIZE_MB = 500  # Skip files larger than this
BATCH_SIZE = 100  # Number of files to process before committing to DB

# Video processing
VIDEO_FRAME_POSITION = 0.5  # Extract frame at 50% of video duration

# API configuration
API_HOST = "0.0.0.0"
API_PORT = 8000
CORS_ORIGINS = [
    "http://localhost:5173",  # Vite default
    "http://localhost:3000",  # Alternative React port
]

# Logging
LOG_LEVEL = "INFO"
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

# Security
def is_path_safe(base_path: str, target_path: str) -> bool:
    """
    Verify that target_path is within base_path to prevent directory traversal
    """
    try:
        base = Path(base_path).resolve()
        target = Path(target_path).resolve()
        return target.is_relative_to(base)
    except (ValueError, OSError):
        return False
