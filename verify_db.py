"""Verify integrity and completeness of Lensa SQLite + media artifacts."""

from __future__ import annotations

import argparse
import sqlite3
from pathlib import Path
from typing import Dict, List, Set, Tuple


DEFAULT_DB_PATH = "museum_guide.db"
DEFAULT_IMAGES_DIR = "images"
DEFAULT_AUDIO_DIR = "audio"
TABLE_WIDTH = 88


class DatabaseVerifier:
    """Perform consistency checks across SQLite metadata, images, and audio files."""

    def __init__(
        self,
        db_path: str = DEFAULT_DB_PATH,
        images_dir: str = DEFAULT_IMAGES_DIR,
        audio_dir: str = DEFAULT_AUDIO_DIR,
    ) -> None:
        """Initialize verifier with repository-relative DB and media directories."""
        self.db_path = Path(db_path)
        self.images_dir = Path(images_dir)
        self.audio_dir = Path(audio_dir)
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row

    def run(self) -> int:
        """Execute checks, print report, and return process exit code."""
        checks = self._collect_checks()
        critical_failures = self._collect_critical_failures(checks=checks)
        self._print_report(checks=checks, critical_failures=critical_failures)
        return 1 if critical_failures else 0

    def close(self) -> None:
        """Close database connection."""
        self.conn.close()

    def _collect_checks(self) -> Dict[str, int]:
        cursor = self.conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM artworks")
        artworks_count = int(cursor.fetchone()[0])

        cursor.execute(
            "SELECT COUNT(*) FROM artworks WHERE image_url IS NOT NULL AND TRIM(image_url) != ''"
        )
        artworks_with_image_url = int(cursor.fetchone()[0])

        cursor.execute(
            """
            SELECT COUNT(*)
            FROM artworks
            WHERE audio_file_path IS NOT NULL AND TRIM(audio_file_path) != ''
            """
        )
        artworks_with_audio_path = int(cursor.fetchone()[0])

        cursor.execute(
            """
            SELECT COUNT(DISTINCT artwork_id)
            FROM artwork_features
            WHERE feature_type = 'orb'
            """
        )
        artworks_with_orb_features = int(cursor.fetchone()[0])

        missing_audio_files, existing_audio_files = self._check_audio_files()
        (
            db_object_ids_count,
            image_file_ids_count,
            missing_image_files_for_db,
            orphan_image_files_on_disk,
        ) = self._check_image_alignment()

        return {
            "artworks_count": artworks_count,
            "artworks_with_image_url": artworks_with_image_url,
            "artworks_with_audio_path": artworks_with_audio_path,
            "artworks_with_orb_features": artworks_with_orb_features,
            "existing_audio_files": existing_audio_files,
            "missing_audio_files": missing_audio_files,
            "db_object_ids_count": db_object_ids_count,
            "image_file_ids_count": image_file_ids_count,
            "missing_image_files_for_db": missing_image_files_for_db,
            "orphan_image_files_on_disk": orphan_image_files_on_disk,
        }

    def _check_audio_files(self) -> Tuple[int, int]:
        cursor = self.conn.cursor()
        cursor.execute(
            """
            SELECT audio_file_path
            FROM artworks
            WHERE audio_file_path IS NOT NULL AND TRIM(audio_file_path) != ''
            """
        )
        rows = cursor.fetchall()
        missing = 0
        existing = 0

        for row in rows:
            raw_path = str(row["audio_file_path"]).strip()
            normalized = raw_path.replace("\\", "/")
            if normalized.startswith("audio/"):
                candidate = Path(normalized)
            else:
                candidate = self.audio_dir / Path(normalized).name

            if candidate.exists():
                existing += 1
            else:
                missing += 1

        return missing, existing

    def _check_image_alignment(self) -> Tuple[int, int, int, int]:
        db_ids = self._load_db_met_object_ids()
        image_ids = self._load_image_met_object_ids()

        missing_images_for_db = len(db_ids - image_ids)
        orphan_images = len(image_ids - db_ids)

        return (
            len(db_ids),
            len(image_ids),
            missing_images_for_db,
            orphan_images,
        )

    def _load_db_met_object_ids(self) -> Set[int]:
        cursor = self.conn.cursor()
        cursor.execute("SELECT met_object_id FROM artworks WHERE met_object_id IS NOT NULL")
        return {int(row[0]) for row in cursor.fetchall()}

    def _load_image_met_object_ids(self) -> Set[int]:
        ids: Set[int] = set()
        if not self.images_dir.exists():
            return ids

        for path in self.images_dir.iterdir():
            if not path.is_file():
                continue
            stem = path.stem.strip()
            if stem.isdigit():
                ids.add(int(stem))
        return ids

    @staticmethod
    def _collect_critical_failures(checks: Dict[str, int]) -> List[str]:
        failures: List[str] = []

        if checks["artworks_count"] == 0:
            failures.append("No artworks found in SQLite.")
        if checks["artworks_with_orb_features"] == 0:
            failures.append("No ORB feature rows linked to artworks.")
        if checks["missing_image_files_for_db"] > 0:
            failures.append("Some DB artworks do not have matching image files in /images.")
        if checks["missing_audio_files"] > 0:
            failures.append("Some DB-referenced audio files are missing on disk.")

        return failures

    def _print_report(self, checks: Dict[str, int], critical_failures: List[str]) -> None:
        print("=" * TABLE_WIDTH)
        print("Lensa Database Health Report")
        print("=" * TABLE_WIDTH)
        print(f"{'Metric':40} | Value")
        print("-" * TABLE_WIDTH)
        print(f"{'Total artworks':40} | {checks['artworks_count']}")
        print(f"{'Artworks with image_url':40} | {checks['artworks_with_image_url']}")
        print(f"{'Artworks with audio_file_path':40} | {checks['artworks_with_audio_path']}")
        print(f"{'Artworks with ORB features':40} | {checks['artworks_with_orb_features']}")
        print(f"{'Existing referenced audio files':40} | {checks['existing_audio_files']}")
        print(f"{'Missing referenced audio files':40} | {checks['missing_audio_files']}")
        print(f"{'DB met_object_id count':40} | {checks['db_object_ids_count']}")
        print(f"{'Image file met_object_id count':40} | {checks['image_file_ids_count']}")
        print(
            f"{'Missing image files for DB IDs':40} | {checks['missing_image_files_for_db']}"
        )
        print(
            f"{'Orphan image files not in DB':40} | {checks['orphan_image_files_on_disk']}"
        )
        print("=" * TABLE_WIDTH)

        if critical_failures:
            print("CRITICAL FAILURES:")
            for failure in critical_failures:
                print(f"- {failure}")
            print("Result: UNHEALTHY")
        else:
            print("Result: HEALTHY")


def parse_args() -> argparse.Namespace:
    """Parse verifier command-line arguments."""
    parser = argparse.ArgumentParser(description="Validate Lensa DB and media integrity.")
    parser.add_argument("--db-path", default=DEFAULT_DB_PATH, help="SQLite database path")
    parser.add_argument("--images-dir", default=DEFAULT_IMAGES_DIR, help="Images directory path")
    parser.add_argument("--audio-dir", default=DEFAULT_AUDIO_DIR, help="Audio directory path")
    return parser.parse_args()


def main() -> None:
    """Run DB integrity verification and exit non-zero on critical failures."""
    args = parse_args()
    verifier = DatabaseVerifier(
        db_path=args.db_path,
        images_dir=args.images_dir,
        audio_dir=args.audio_dir,
    )
    try:
        exit_code = verifier.run()
    finally:
        verifier.close()
    raise SystemExit(exit_code)


if __name__ == "__main__":
    main()
