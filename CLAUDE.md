# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Image & Video Deduplicator** - A full-stack web application for detecting and removing duplicate or similar images and videos using perceptual hashing. The system compares files by visual content, not just file metadata, enabling detection of similar images even with different resolutions or formats.

## Technology Stack

### Backend
- **FastAPI**: Async Python web framework for REST API
- **Pillow**: Image processing and manipulation
- **imagehash**: Perceptual hashing algorithms (pHash)
- **OpenCV**: Video processing and frame extraction
- **SQLite + aiosqlite**: Async database for caching file hashes
- **Pydantic**: Data validation and settings management

### Frontend
- **React 19**: UI framework with hooks
- **Vite**: Build tool and dev server
- **Tailwind CSS**: Utility-first styling
- **Axios**: HTTP client for API communication

## Development Commands

### Frontend
```bash
# Start development server with HMR
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview

# Run ESLint
npm run lint
```

### Backend
```bash
cd backend

# Create and activate virtual environment (first time)
python -m venv venv
venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/Mac

# Install dependencies
pip install -r requirements.txt

# Run development server
python main.py

# Run with auto-reload
uvicorn main:app --reload
```

## Architecture

### High-Level Flow

1. **Scan Phase**: User provides folder path → Backend recursively scans files → Extracts metadata and computes perceptual hashes → Stores in SQLite cache
2. **Compare Phase**: Backend compares all hashes pairwise using Hamming distance → Returns pairs below similarity threshold
3. **Delete Phase**: User selects file to delete → Backend validates path is within scanned directory → Deletes file and removes from database

### Backend Architecture

#### Core Modules
- **main.py** (backend:1): FastAPI application with all API endpoints, CORS configuration, and lifespan management
- **scanner.py** (backend:1): File system scanning, metadata extraction, hash computation
- **comparator.py** (backend:1): Perceptual hash comparison using Hamming distance
- **database.py** (backend:1): SQLite operations with async support via aiosqlite
- **models.py** (backend:1): Pydantic models for request/response validation
- **config.py** (backend:1): Configuration constants and path validation

#### Key Algorithms

**Perceptual Hashing (scanner.py:88-106)**:
- Resizes image to standard size
- Converts to grayscale
- Computes DCT (Discrete Cosine Transform)
- Generates 64-bit hash representing low-frequency components
- Videos: extracts frame at 50% duration, then applies same algorithm

**Similarity Detection (comparator.py:14-28)**:
- Computes Hamming distance between two hashes (number of differing bits)
- Threshold of 0 = identical, 5 = very similar, 15 = loosely similar
- Lower distance = higher similarity

**Security (config.py:48-58)**:
- `is_path_safe()` validates that target path is within base path
- Prevents directory traversal attacks
- All delete operations validate against scanned base path

#### Database Schema (database.py:25-41)

Table: `files`
- `id`: Primary key
- `path`: Unique file path (indexed)
- `filename`: File name
- `size_bytes`: File size
- `width`, `height`: Dimensions
- `created_at`, `modified_at`: Timestamps
- `file_type`: 'image' or 'video'
- `hash`: Perceptual hash (indexed)
- `scan_date`: Last scan timestamp

Cache Strategy: If file's modified_at hasn't changed, use cached hash instead of recomputing

#### API Endpoints (main.py)

- `POST /api/scan`: Start background scan (returns immediately, scan runs async)
- `GET /api/scan/status`: Poll scan progress (total files, processed count, errors)
- `GET /api/duplicates?threshold=5`: Get pairs of similar files
- `POST /api/delete`: Delete file with path validation
- `GET /api/stats`: Database statistics (file counts, total size)
- `DELETE /api/cache`: Clear all cached data

### Frontend Architecture

#### Component Hierarchy

```
App.jsx (root state management)
├── Stats.jsx (database statistics)
├── Scanner.jsx (folder input, threshold slider, scan trigger)
├── Progress.jsx (real-time scan progress, errors)
└── ImagePair.jsx (side-by-side comparison)
    └── FileInfo.jsx (metadata display)
```

#### State Management (App.jsx:11-16)

Global state in `App.jsx`:
- `isScanning`: Boolean for scan in progress
- `scanBasePath`: Base path for security validation
- `currentThreshold`: Similarity threshold
- `duplicates`: Array of DuplicatePair objects
- `totalSavings`: Calculated potential space savings
- `loading`: Loading state for API calls

#### Key Features

**Real-time Progress (Progress.jsx:9-25)**:
- Polls `/api/scan/status` every 1 second
- Updates progress bar based on processed/total files
- Shows current file being processed
- Displays errors as they occur
- Automatically stops polling when scan completes

**Delete Workflow (ImagePair.jsx:8-28)**:
- Confirms deletion with browser native confirm()
- Sends DELETE request with file path and base path
- On success, removes pair from local state
- On error, displays error message
- Prevents deletion while another delete is in progress

## Configuration

### Backend (backend/config.py)

```python
SUPPORTED_EXTENSIONS = {'.jpg', '.png', '.gif', '.mp4', '.mov', ...}
MAX_FILE_SIZE_MB = 500  # Skip files larger than this
HASH_SIZE = 8  # 8x8 = 64-bit hash
DEFAULT_SIMILARITY_THRESHOLD = 5
VIDEO_FRAME_POSITION = 0.5  # Extract frame at 50% duration
```

### Frontend API URL

All components use `http://localhost:8000` as API_URL. For production, update this in:
- src/components/Scanner.jsx:4
- src/components/Progress.jsx:4
- src/components/ImagePair.jsx:5
- src/components/Stats.jsx:4
- src/App.jsx:8

## Important Implementation Details

### Async Scanning (scanner.py:174-195)

Scanning runs in background via FastAPI BackgroundTasks. Global `scan_status` object tracks state. Only one scan can run at a time (raises RuntimeError if scan already in progress).

### Pairwise Comparison (comparator.py:57-91)

Compares all files against all other files (O(n²) complexity). Uses set to track compared pairs and avoid duplicates. For 1000 files, performs ~500,000 comparisons.

**Performance consideration**: Large directories (>5000 files) may require optimization (e.g., LSH, clustering).

### Image Preview Limitations (ImagePair.jsx:37-40)

Uses `file://` URLs for local preview. Browser security may block this. Fallback message shown on error. This is a browser limitation, not a bug.

### CORS Configuration (main.py:50-56)

CORS allows requests from:
- http://localhost:5173 (Vite default)
- http://localhost:3000 (alternative)

For production, update `CORS_ORIGINS` in backend/config.py.

## Testing Strategy

### Backend Testing
- Test path validation with directory traversal attempts
- Test hash computation consistency across runs
- Test comparison accuracy with known similar/dissimilar images
- Test database caching (same file should use cached hash)

### Frontend Testing
- Test scan progress updates
- Test error handling for invalid paths
- Test delete confirmation flow
- Test threshold slider updates

## Deployment Considerations

### Production Backend
- Use Gunicorn/Uvicorn with multiple workers
- Set appropriate `MAX_FILE_SIZE_MB` for your use case
- Consider adding authentication for multi-user scenarios
- Enable HTTPS if exposing API beyond localhost

### Production Frontend
- Update API_URL to production backend
- Build with `npm run build`
- Serve `dist/` folder with nginx/apache
- Consider adding image preview proxy to bypass browser restrictions

## Common Development Tasks

### Adding New File Format Support
1. Add extension to `IMAGE_EXTENSIONS` or `VIDEO_EXTENSIONS` in backend/config.py
2. No other changes needed (scanner auto-detects based on extension)

### Adjusting Hash Algorithm
1. Modify `HASH_SIZE` in backend/config.py (default 8 = 64 bits)
2. Clear database cache: `DELETE http://localhost:8000/api/cache`
3. Re-scan to regenerate hashes

### Changing Video Frame Position
1. Modify `VIDEO_FRAME_POSITION` in backend/config.py (0.0-1.0)
2. Clear cache and re-scan

### Adding New Comparison Algorithm
1. Implement in comparator.py (e.g., `dhash`, `ahash`)
2. Update scanner.py to compute additional hash
3. Store in new database column
4. Update comparison logic to use new hash

## Known Limitations

- Large directories (>10,000 files) may have slow comparison phase
- Perceptual hashing doesn't detect rotated/flipped images
- Video comparison only uses single frame (middle of video)
- Browser security prevents image preview in some cases
- No undo functionality for deletions (permanent)

## Data Flow Example

```
User enters: "C:\Photos"
    ↓
POST /api/scan {"path": "C:\\Photos", "similarity_threshold": 5}
    ↓
Background: scanner.py finds 100 images
    ↓
For each file:
  - Extract metadata (size, dimensions, dates)
  - Compute perceptual hash
  - Store in SQLite
    ↓
Poll GET /api/scan/status every 1s → "50/100 processed"
    ↓
Scan completes → GET /api/duplicates?threshold=5
    ↓
comparator.py compares all 100 files pairwise
  - 4,950 comparisons (100*99/2)
  - Returns pairs with Hamming distance ≤ 5
    ↓
Frontend displays pairs side-by-side
    ↓
User clicks "Delete This File" on file1.jpg
    ↓
POST /api/delete {"file_path": "C:\\Photos\\file1.jpg", "scan_base_path": "C:\\Photos"}
    ↓
Backend validates path is within C:\Photos
    ↓
Delete file from disk + remove from database
    ↓
Frontend refreshes duplicate list
```
