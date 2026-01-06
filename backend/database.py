"""
SQLite database layer for caching file information and hashes
"""
import aiosqlite
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict
from config import DB_PATH, DATA_DIR

logger = logging.getLogger(__name__)


class Database:
    def __init__(self, db_path: Path = DB_PATH):
        self.db_path = db_path
        self.connection: Optional[aiosqlite.Connection] = None

    async def initialize(self):
        """Create database tables if they don't exist"""
        # Ensure data directory exists
        DATA_DIR.mkdir(parents=True, exist_ok=True)

        self.connection = await aiosqlite.connect(self.db_path)
        await self.connection.execute("""
            CREATE TABLE IF NOT EXISTS files (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                path TEXT UNIQUE NOT NULL,
                filename TEXT NOT NULL,
                size_bytes INTEGER NOT NULL,
                width INTEGER,
                height INTEGER,
                created_at TIMESTAMP NOT NULL,
                modified_at TIMESTAMP NOT NULL,
                file_type TEXT NOT NULL,
                hash TEXT,
                scan_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(path)
            )
        """)

        await self.connection.execute("""
            CREATE INDEX IF NOT EXISTS idx_hash ON files(hash)
        """)

        await self.connection.execute("""
            CREATE INDEX IF NOT EXISTS idx_path ON files(path)
        """)

        await self.connection.commit()
        logger.info(f"Database initialized at {self.db_path}")

    async def close(self):
        """Close database connection"""
        if self.connection:
            await self.connection.close()
            logger.info("Database connection closed")

    async def get_file_by_path(self, path: str) -> Optional[Dict]:
        """Get cached file information by path"""
        async with self.connection.execute(
            "SELECT * FROM files WHERE path = ?", (path,)
        ) as cursor:
            row = await cursor.fetchone()
            if row:
                columns = [desc[0] for desc in cursor.description]
                return dict(zip(columns, row))
            return None

    async def insert_or_update_file(self, file_data: Dict) -> int:
        """Insert or update file information"""
        query = """
            INSERT INTO files (
                path, filename, size_bytes, width, height,
                created_at, modified_at, file_type, hash
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(path) DO UPDATE SET
                size_bytes = excluded.size_bytes,
                width = excluded.width,
                height = excluded.height,
                modified_at = excluded.modified_at,
                hash = excluded.hash,
                scan_date = CURRENT_TIMESTAMP
        """

        cursor = await self.connection.execute(query, (
            file_data['path'],
            file_data['filename'],
            file_data['size_bytes'],
            file_data.get('width'),
            file_data.get('height'),
            file_data['created_at'],
            file_data['modified_at'],
            file_data['file_type'],
            file_data.get('hash')
        ))
        await self.connection.commit()
        return cursor.lastrowid

    async def get_all_files(self) -> List[Dict]:
        """Get all cached files"""
        async with self.connection.execute("SELECT * FROM files") as cursor:
            rows = await cursor.fetchall()
            columns = [desc[0] for desc in cursor.description]
            return [dict(zip(columns, row)) for row in rows]

    async def get_files_with_hashes(self, file_type: str = 'both') -> List[Dict]:
        """Get all files that have computed hashes

        Args:
            file_type: 'image', 'video', or 'both' to filter by type
        """
        if file_type == 'both':
            query = "SELECT * FROM files WHERE hash IS NOT NULL ORDER BY hash"
            params = ()
        else:
            query = "SELECT * FROM files WHERE hash IS NOT NULL AND file_type = ? ORDER BY hash"
            params = (file_type,)

        async with self.connection.execute(query, params) as cursor:
            rows = await cursor.fetchall()
            columns = [desc[0] for desc in cursor.description]
            return [dict(zip(columns, row)) for row in rows]

    async def delete_file_record(self, path: str) -> bool:
        """Delete file record from database"""
        cursor = await self.connection.execute(
            "DELETE FROM files WHERE path = ?", (path,)
        )
        await self.connection.commit()
        return cursor.rowcount > 0

    async def get_stats(self) -> Dict:
        """Get database statistics"""
        async with self.connection.execute("""
            SELECT
                COUNT(*) as total_files,
                SUM(CASE WHEN file_type = 'image' THEN 1 ELSE 0 END) as total_images,
                SUM(CASE WHEN file_type = 'video' THEN 1 ELSE 0 END) as total_videos,
                SUM(size_bytes) as total_size_bytes,
                MIN(scan_date) as earliest_scan
            FROM files
        """) as cursor:
            row = await cursor.fetchone()
            if row:
                return {
                    'total_files_cached': row[0] or 0,
                    'total_images': row[1] or 0,
                    'total_videos': row[2] or 0,
                    'total_size_mb': (row[3] or 0) / (1024 * 1024),
                    'cache_created_at': row[4]
                }
            return {
                'total_files_cached': 0,
                'total_images': 0,
                'total_videos': 0,
                'total_size_mb': 0.0,
                'cache_created_at': None
            }

    async def clear_all(self):
        """Clear all records from database (for testing/reset)"""
        await self.connection.execute("DELETE FROM files")
        await self.connection.commit()
        logger.warning("All database records cleared")


# Global database instance
db = Database()
