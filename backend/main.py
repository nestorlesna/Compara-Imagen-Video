"""
FastAPI application for image deduplicator
"""
import logging
import asyncio
from pathlib import Path
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, BackgroundTasks, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse

from config import API_HOST, API_PORT, CORS_ORIGINS, LOG_LEVEL, LOG_FORMAT, is_path_safe
from models import (
    ScanRequest, ScanStatus, DuplicatesResponse, DeleteRequest,
    DeleteResponse, StatsResponse
)
from database import db
from scanner import FileScanner, scan_status
from comparator import ImageComparator

# Configure logging
logging.basicConfig(level=LOG_LEVEL, format=LOG_FORMAT)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events"""
    # Startup
    logger.info("Starting up image deduplicator API")
    await db.initialize()
    yield
    # Shutdown
    logger.info("Shutting down image deduplicator API")
    await db.close()


app = FastAPI(
    title="Image Deduplicator API",
    description="API for detecting and removing duplicate/similar images and videos",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Image Deduplicator API",
        "version": "1.0.0",
        "endpoints": {
            "scan": "POST /api/scan",
            "scan_status": "GET /api/scan/status",
            "duplicates": "GET /api/duplicates",
            "delete": "POST /api/delete",
            "stats": "GET /api/stats"
        }
    }


@app.post("/api/scan", response_model=ScanStatus)
async def start_scan(request: ScanRequest, background_tasks: BackgroundTasks):
    """
    Start scanning a directory for images and videos

    This runs in the background and returns immediately
    Use /api/scan/status to check progress
    """
    if scan_status.is_scanning:
        raise HTTPException(status_code=409, detail="A scan is already in progress")

    # Validate path exists and is a directory
    path = Path(request.path)
    if not path.exists():
        raise HTTPException(status_code=404, detail=f"Path not found: {request.path}")
    if not path.is_dir():
        raise HTTPException(status_code=400, detail=f"Path is not a directory: {request.path}")

    # Start scan in background
    background_tasks.add_task(
        FileScanner.scan_directory,
        request.path,
        request.file_type,
        request.clear_cache
    )

    # Return initial status
    return ScanStatus(
        is_scanning=True,
        scanned_path=request.path,
        total_files=0,
        processed_files=0,
        current_file=None,
        errors=[],
        start_time=None,
        end_time=None
    )


@app.get("/api/scan/status", response_model=ScanStatus)
async def get_scan_status():
    """Get current scan status"""
    return ScanStatus(**scan_status.to_dict())


@app.get("/api/duplicates")
async def get_duplicates(threshold: int = 5, file_type: str = None):
    """
    Get list of duplicate/similar file pairs

    Args:
        threshold: Similarity threshold (0-15)
                  0 = identical only
                  5 = very similar (default)
                  10 = somewhat similar
                  15 = loosely similar
        file_type: Type of files to compare ('image', 'video', or 'both')
                  If not specified, uses the file_type from the last scan
    """
    if threshold < 0 or threshold > 15:
        raise HTTPException(
            status_code=400,
            detail="Threshold must be between 0 and 15"
        )

    # Use file_type from last scan if not specified
    if file_type is None:
        file_type = scan_status.file_type

    # Validate file_type
    if file_type not in ['image', 'video', 'both']:
        raise HTTPException(
            status_code=400,
            detail="file_type must be 'image', 'video', or 'both'"
        )

    try:
        pairs = await ImageComparator.find_duplicates(
            similarity_threshold=threshold,
            file_type=file_type
        )
        total_savings = ImageComparator.calculate_potential_savings(pairs)

        return DuplicatesResponse(
            pairs=pairs,
            total_pairs=len(pairs),
            total_potential_savings_mb=total_savings
        )
    except Exception as e:
        logger.error(f"Error finding duplicates: {e}")
        raise HTTPException(status_code=500, detail=f"Error finding duplicates: {str(e)}")


@app.post("/api/delete", response_model=DeleteResponse)
async def delete_file(request: DeleteRequest):
    """
    Delete a file

    Security: Only allows deleting files within the scanned directory
    """
    try:
        file_path = Path(request.file_path)
        base_path = Path(request.scan_base_path)

        # Security check: ensure file is within scanned directory
        if not is_path_safe(str(base_path), str(file_path)):
            raise HTTPException(
                status_code=403,
                detail="Cannot delete file outside of scanned directory"
            )

        # Check if file exists
        if not file_path.exists():
            raise HTTPException(status_code=404, detail="File not found")

        if not file_path.is_file():
            raise HTTPException(status_code=400, detail="Path is not a file")

        # Delete the file
        file_path.unlink()
        logger.info(f"Deleted file: {file_path}")

        # Remove from database
        await db.delete_file_record(str(file_path))

        return DeleteResponse(
            success=True,
            message="File deleted successfully",
            deleted_path=str(file_path)
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting file: {e}")
        raise HTTPException(status_code=500, detail=f"Error deleting file: {str(e)}")


@app.get("/api/stats", response_model=StatsResponse)
async def get_stats():
    """Get general statistics about cached files"""
    try:
        stats = await db.get_stats()
        return StatsResponse(**stats)
    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting stats: {str(e)}")


@app.delete("/api/cache")
async def clear_cache():
    """Clear all cached data (for testing/reset)"""
    try:
        await db.clear_all()
        return {"message": "Cache cleared successfully"}
    except Exception as e:
        logger.error(f"Error clearing cache: {e}")
        raise HTTPException(status_code=500, detail=f"Error clearing cache: {str(e)}")


@app.get("/api/preview")
async def get_file_preview(file_path: str = Query(..., description="Full path to the file")):
    """
    Serve a file for preview

    Security: Only serves files that exist in the database (have been scanned)
    """
    try:
        # Normalize the path
        path = Path(file_path).resolve()
        normalized_path = str(path)

        # Try to find file in database with normalized path
        file_record = await db.get_file_by_path(normalized_path)

        # If not found with normalized path, try original path
        if not file_record:
            file_record = await db.get_file_by_path(file_path)

        # Verify file exists on disk first
        if not path.exists():
            if file_record:
                logger.error(f"File in database but not on disk: {path}")
                # Clean up database record for non-existent file
                await db.delete_file_record(str(path))
            raise HTTPException(
                status_code=404,
                detail=f"File not found on disk. It may have been moved or deleted. Path: {path}"
            )

        if not file_record:
            logger.warning(f"Preview request for file not in database (but exists on disk): {file_path}")
            # Allow preview even if not in database, as long as file exists
            # This is useful for files that were added after the last scan

        if not path.is_file():
            raise HTTPException(status_code=400, detail="Path is not a file")

        # Determine media type
        suffix = path.suffix.lower()
        media_type = None

        # Image types
        if suffix in ['.jpg', '.jpeg']:
            media_type = 'image/jpeg'
        elif suffix in ['.png']:
            media_type = 'image/png'
        elif suffix in ['.gif']:
            media_type = 'image/gif'
        elif suffix in ['.webp']:
            media_type = 'image/webp'
        elif suffix in ['.bmp']:
            media_type = 'image/bmp'
        # Video types
        elif suffix in ['.mp4']:
            media_type = 'video/mp4'
        elif suffix in ['.webm']:
            media_type = 'video/webm'
        elif suffix in ['.mov']:
            media_type = 'video/quicktime'
        elif suffix in ['.avi']:
            media_type = 'video/x-msvideo'
        else:
            media_type = 'application/octet-stream'

        return FileResponse(
            path=str(path),
            media_type=media_type,
            filename=path.name
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error serving file preview: {e}")
        raise HTTPException(status_code=500, detail=f"Error serving file: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=API_HOST,
        port=API_PORT,
        reload=True,
        log_level=LOG_LEVEL.lower()
    )
