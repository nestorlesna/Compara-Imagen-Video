# Image & Video Deduplicator

A web application for detecting and removing duplicate or similar images and videos in your local file system. Uses perceptual hashing to find visually similar content, not just identical files.

## Features

- 🔍 **Recursive Scanning**: Scans folders and all subfolders
- 🎯 **Perceptual Hashing**: Finds similar images, not just identical ones
- 🎬 **Video Support**: Extracts representative frames from videos for comparison
- 💾 **Smart Caching**: SQLite database caches results to avoid reprocessing
- 🎚️ **Configurable Threshold**: Adjust similarity detection sensitivity
- 🖼️ **Side-by-Side Comparison**: Visual interface to compare and choose which file to keep
- 🔒 **Security**: Prevents accidental deletion outside scanned directory
- 📊 **Statistics**: View totals and potential space savings

## Supported Formats

**Images**: `.jpg`, `.jpeg`, `.png`, `.gif`, `.bmp`, `.webp`, `.tiff`
**Videos**: `.mp4`, `.avi`, `.mov`, `.mkv`, `.webm`, `.flv`, `.wmv`

## Architecture

### Backend (Python + FastAPI)
- **FastAPI**: REST API server
- **Pillow**: Image processing
- **imagehash**: Perceptual hashing (pHash, dHash, aHash)
- **OpenCV**: Video frame extraction
- **SQLite**: Result caching
- **aiosqlite**: Async database operations

### Frontend (React + Vite)
- **React 19**: UI framework
- **Vite**: Build tool and dev server
- **Tailwind CSS**: Styling
- **Axios**: API communication

## Installation

### Prerequisites

- Python 3.8 or higher
- Node.js 16 or higher
- npm or yarn

### Backend Setup

1. Navigate to the backend directory:
```bash
cd backend
```

2. Create a virtual environment (recommended):
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/Mac
python3 -m venv venv
source venv/bin/activate
```

3. Install Python dependencies:
```bash
pip install -r requirements.txt
```

### Frontend Setup

1. Install Node.js dependencies (from project root):
```bash
npm install
```

## Usage

### 1. Start the Backend Server

From the `backend` directory:

```bash
python main.py
```

The API will be available at `http://localhost:8000`

You can verify it's running by visiting `http://localhost:8000` in your browser.

### 2. Start the Frontend Development Server

From the project root:

```bash
npm run dev
```

The web interface will open at `http://localhost:5173`

### 3. Using the Application

1. **Enter Folder Path**: Input the full path to the folder you want to scan
   - Example (Windows): `C:\Users\YourName\Pictures`
   - Example (Linux/Mac): `/home/yourname/Pictures`

2. **Adjust Similarity Threshold** (optional):
   - `0` = Only identical files
   - `5` = Very similar (default, recommended)
   - `10` = Somewhat similar
   - `15` = Loosely similar

3. **Click "Start Scan"**: The app will:
   - Recursively scan all files
   - Extract metadata and compute perceptual hashes
   - Cache results in SQLite database

4. **Review Results**:
   - View duplicate pairs side-by-side
   - See file details (size, dimensions, dates)
   - Similarity percentage for each pair

5. **Delete Files**:
   - Click "Delete This File" under the file you want to remove
   - Confirm the deletion
   - File is permanently deleted from disk

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | API information |
| POST | `/api/scan` | Start directory scan |
| GET | `/api/scan/status` | Get scan progress |
| GET | `/api/duplicates?threshold=5` | Get duplicate pairs |
| POST | `/api/delete` | Delete a file |
| GET | `/api/stats` | Get database statistics |
| GET | `/api/preview?file_path=<path>` | Serve file for preview (images/videos) |
| DELETE | `/api/cache` | Clear cache (reset) |

## Configuration

### Backend Configuration

Edit `backend/config.py` to customize:

- Supported file extensions
- Maximum file size
- Hash algorithm parameters
- Similarity thresholds
- Video frame extraction position

### Frontend Configuration

Edit `src/components/Scanner.jsx` to change:

- API URL (if not localhost)
- Default threshold value

## How It Works

### Perceptual Hashing (pHash) Algorithm

Unlike traditional MD5/SHA hashing that only detects **identical** files byte-by-byte, perceptual hashing creates a "fingerprint" of the **visual content**, allowing detection of similar images even with different resolutions, formats, or slight modifications.

#### For Images (Implementation in `backend/scanner.py:88-106`):

1. **Preprocessing**:
   - Resize image to 8x8 pixels (configurable via `HASH_SIZE` in config)
   - Convert to grayscale to eliminate color variations
   - This reduces the image to essential visual structure

2. **DCT (Discrete Cosine Transform)**:
   - Applies frequency-domain transformation
   - Separates the image into high-frequency (details, noise) and low-frequency (structure, shapes) components
   - Focuses on low-frequency components that represent perceptual content
   - This is why the algorithm detects similar images despite compression or minor edits

3. **Hash Generation**:
   - Calculates the median of all DCT coefficients
   - Generates a 64-bit binary hash:
     - Bit = `1` if coefficient > median
     - Bit = `0` if coefficient ≤ median
   - Result: A compact fingerprint like `a8f3c2d1b4e7f9a2` (hexadecimal)

4. **Example**:
   ```
   Original Image (1920x1080 JPG) → Hash: 1010101010101010...
   Same Image (640x480 PNG)       → Hash: 1010111010101010...
   Different Image                → Hash: 0101011101010101...
   ```

#### For Videos (Implementation in `backend/scanner.py:140-165`):

1. Opens the video file using OpenCV (`cv2.VideoCapture`)
2. Extracts **one frame at 50% duration** (`VIDEO_FRAME_POSITION = 0.5`)
   - Uses middle frame as representative sample
   - Configurable in `backend/config.py`
3. Converts frame to PIL Image
4. Applies **same pHash algorithm** as images
5. Compares videos based on this single representative frame

### Similarity Detection (Implementation in `backend/comparator.py:14-28`)

#### Hamming Distance Calculation:

The algorithm compares two hashes using **Hamming distance**: the count of differing bits.

```python
# Example comparison
hash1 = "1010101010101010..."  # 64 bits
hash2 = "1010111010101010..."  # 64 bits

# XOR operation reveals differences
difference = hash1 XOR hash2
# Result: 0000010000000000... (only bit 5 differs)

hamming_distance = count_ones(difference)  # = 1
```

#### Threshold Interpretation:

| Threshold | Meaning | Use Case |
|-----------|---------|----------|
| **0** | Identical | Only pixel-perfect matches |
| **1-3** | Nearly identical | Minor compression/resize |
| **5** (default) | Very similar | Same photo, different quality |
| **8-10** | Similar | Same scene, different angle/crop |
| **12-15** | Loosely similar | Similar composition/subject |

#### Comparison Complexity:

- **Algorithm**: Pairwise comparison O(n²)
- **For 1,000 files**: ~500,000 comparisons
- **Optimization**: Each comparison is just XOR of 64-bit integers (extremely fast)
- **Performance**: 10,000 files ≈ 50M comparisons ≈ few seconds

### Why This Works

✅ **Detects similarity through**:
- Different resolutions (4K vs HD vs thumbnail)
- Different formats (JPG vs PNG vs WebP)
- Compression artifacts (high quality vs low quality JPG)
- Minor color/brightness adjustments
- Small crops or borders

❌ **Cannot detect**:
- **Rotations** (90°, 180°, 270° turns)
- **Flips** (horizontal/vertical mirroring)
- **Significant crops** (>30% of image removed)
- **Perspective changes** (different camera angles)
- **Content changes** (adding/removing objects)

### Caching Strategy (Implementation in `backend/database.py`)

To avoid reprocessing:
1. After computing a hash, stores it in SQLite with file metadata
2. Before recomputing, checks if file's `modified_at` timestamp changed
3. If unchanged, reuses cached hash (**~1000x faster**)
4. Database schema includes indexed `hash` and `path` columns

### Libraries Used

- **`imagehash`** (Python): Production-ready pHash implementation
- **`Pillow`** (PIL): Image I/O and preprocessing
- **`OpenCV`** (cv2): Video frame extraction
- **`numpy`**: DCT computation and numerical operations

### Code References

- **Hash computation**: `backend/scanner.py:88-106` (images), `140-165` (videos)
- **Comparison logic**: `backend/comparator.py:14-28` (Hamming distance)
- **Database caching**: `backend/database.py:59-68` (cache lookup)
- **Configuration**: `backend/config.py` (thresholds, hash size, frame position)

## Security Features

- **Path Validation**: Only allows deletion within scanned directory
- **Confirmation**: Requires user confirmation before deletion
- **No Network Access**: All operations are 100% local
- **Read-Only Scanning**: Scanning doesn't modify files

## Troubleshooting

### Backend won't start

**Issue**: `ModuleNotFoundError`
**Solution**: Make sure you activated the virtual environment and installed dependencies

**Issue**: `Permission denied`
**Solution**: Run with appropriate permissions or scan a folder you own

### Frontend can't connect to backend

**Issue**: `Network Error` or CORS errors
**Solution**: Ensure backend is running on port 8000 and frontend on 5173

### Images or videos not displaying

**Issue**: Files don't appear in preview
**Solution**: Ensure the file exists in the database (was part of a scan). The `/api/preview` endpoint only serves scanned files for security.

### Scan takes too long

**Issue**: Large folders with many files
**Solution**:
- Use SQLite cache (subsequent scans are faster)
- Increase `MAX_FILE_SIZE_MB` to skip large files
- Scan smaller subdirectories

## Development

### Project Structure

```
.
├── backend/
│   ├── main.py              # FastAPI application
│   ├── scanner.py           # File scanning logic
│   ├── comparator.py        # Image comparison
│   ├── database.py          # SQLite operations
│   ├── models.py            # Pydantic models
│   ├── config.py            # Configuration
│   └── requirements.txt     # Python dependencies
├── src/
│   ├── components/
│   │   ├── Scanner.jsx      # Scan initiation
│   │   ├── Progress.jsx     # Progress tracking
│   │   ├── ImagePair.jsx    # Pair comparison view
│   │   ├── FileInfo.jsx     # File metadata display
│   │   └── Stats.jsx        # Statistics dashboard
│   ├── App.jsx              # Main application
│   └── main.jsx             # Entry point
├── data/                    # SQLite database location
└── README.md
```

### Running Tests

```bash
# Backend
cd backend
pytest

# Frontend
npm run test
```

### Building for Production

```bash
# Frontend
npm run build

# Backend
# Use gunicorn or uvicorn with appropriate workers
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

## Limitations

- **Rotation/flip detection**: Does not detect rotated or mirrored versions of the same image
- **Large files**: Very large images/videos (>100MB) may require significant processing time
- **Video comparison**: Only compares a single frame (middle of video), may miss differences in other parts
- **Perspective changes**: Cannot detect the same subject photographed from different angles
- **Performance**: For 10,000+ files, comparison phase may take several minutes (O(n²) complexity)

## Future Enhancements

- Rotation/flip detection
- Batch delete operations
- Export results to CSV
- Undo delete functionality
- Multi-threaded scanning
- Progress persistence across sessions

## License

MIT License - See LICENSE file for details

## Contributing

Contributions are welcome! Please open an issue or submit a pull request.

## Acknowledgments

- [imagehash](https://github.com/JohannesBuchner/imagehash) - Perceptual hashing library
- [FastAPI](https://fastapi.tiangolo.com/) - Modern Python web framework
- [React](https://react.dev/) - UI library
- [Tailwind CSS](https://tailwindcss.com/) - Styling framework
