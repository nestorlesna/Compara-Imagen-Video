"""
Image comparison logic using perceptual hashing
"""
import logging
from typing import List, Dict, Tuple
from datetime import datetime
import imagehash
from database import db
from models import FileInfo, DuplicatePair

logger = logging.getLogger(__name__)


class ImageComparator:
    """Compare images using perceptual hashing and Hamming distance"""

    @staticmethod
    def hamming_distance(hash1: str, hash2: str) -> int:
        """
        Calculate Hamming distance between two hex hash strings
        Returns the number of differing bits
        """
        try:
            h1 = imagehash.hex_to_hash(hash1)
            h2 = imagehash.hex_to_hash(hash2)
            return h1 - h2  # imagehash overloads - operator for Hamming distance
        except Exception as e:
            logger.error(f"Error calculating Hamming distance: {e}")
            return 999  # Return high value on error

    @staticmethod
    def calculate_similarity_percentage(hamming_distance: int, hash_size: int = 8) -> float:
        """
        Convert Hamming distance to similarity percentage
        hash_size=8 means 64 bits total (8x8)
        """
        max_distance = hash_size * hash_size
        similarity = (1 - (hamming_distance / max_distance)) * 100
        return round(similarity, 2)

    @staticmethod
    def db_row_to_file_info(row: Dict) -> FileInfo:
        """Convert database row to FileInfo model"""
        return FileInfo(
            path=row['path'],
            filename=row['filename'],
            size_mb=round(row['size_bytes'] / (1024 * 1024), 2),
            width=row.get('width'),
            height=row.get('height'),
            created_at=datetime.fromisoformat(row['created_at']) if isinstance(row['created_at'], str) else row['created_at'],
            modified_at=datetime.fromisoformat(row['modified_at']) if isinstance(row['modified_at'], str) else row['modified_at'],
            file_type=row['file_type'],
            hash=row.get('hash')
        )

    @staticmethod
    async def find_duplicates(similarity_threshold: int = 5, file_type: str = 'both') -> List[DuplicatePair]:
        """
        Find all duplicate/similar pairs based on perceptual hash similarity

        Args:
            similarity_threshold: Maximum Hamming distance to consider as duplicate
                                0 = identical only
                                5 = very similar (default)
                                10 = somewhat similar
                                15 = loosely similar
            file_type: Type of files to compare ('image', 'video', or 'both')

        Returns:
            List of DuplicatePair objects
        """
        logger.info(f"Finding duplicates with threshold={similarity_threshold}, file_type={file_type}")

        # Get all files with hashes, filtered by type
        files = await db.get_files_with_hashes(file_type=file_type)
        logger.info(f"Comparing {len(files)} files")

        pairs = []
        compared = set()  # Track compared pairs to avoid duplicates

        # Compare all files pairwise
        for i in range(len(files)):
            for j in range(i + 1, len(files)):
                file1 = files[i]
                file2 = files[j]

                # Skip if already compared
                pair_key = tuple(sorted([file1['path'], file2['path']]))
                if pair_key in compared:
                    continue
                compared.add(pair_key)

                # Skip if either file doesn't have a hash
                if not file1.get('hash') or not file2.get('hash'):
                    continue

                # Calculate similarity
                distance = ImageComparator.hamming_distance(file1['hash'], file2['hash'])

                # If similar enough, add to pairs
                if distance <= similarity_threshold:
                    similarity_pct = ImageComparator.calculate_similarity_percentage(distance)

                    pair = DuplicatePair(
                        file1=ImageComparator.db_row_to_file_info(file1),
                        file2=ImageComparator.db_row_to_file_info(file2),
                        similarity_score=distance,
                        similarity_percentage=similarity_pct
                    )
                    pairs.append(pair)

        # Sort by similarity (most similar first)
        pairs.sort(key=lambda p: p.similarity_score)

        logger.info(f"Found {len(pairs)} duplicate/similar pairs")
        return pairs

    @staticmethod
    def calculate_potential_savings(pairs: List[DuplicatePair]) -> float:
        """
        Calculate total potential disk space savings if one file from each pair is deleted
        Takes the larger file from each pair
        """
        total_mb = 0.0
        for pair in pairs:
            # Take the larger file as potential savings
            larger_size = max(pair.file1.size_mb, pair.file2.size_mb)
            total_mb += larger_size
        return round(total_mb, 2)
