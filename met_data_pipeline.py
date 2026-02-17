"""
Lensa data pipeline for The Met Museum API.

What this script does:
1. Connects to The Met Collection API.
2. Collects a pool of highlight artworks (fame proxy) and keeps the top 100.
3. Saves title, artist, date, medium, department, image_url into SQLite.
4. Downloads artwork images into ./images.
5. Shows progress with tqdm.
6. Handles API/download/database errors gracefully.
7. Prints a final summary.
"""

from __future__ import annotations

import argparse
import sqlite3
import time
from pathlib import Path
from typing import Dict, List, Optional
from urllib.parse import urlparse

import requests
from tqdm import tqdm


class MetDataPipeline:
    BASE_URL = "https://collectionapi.metmuseum.org/public/collection/v1"

    # Curated terms used with isHighlight=true to pull highly known pieces.
    HIGHLIGHT_QUERIES = [
        "van gogh",
        "vermeer",
        "rembrandt",
        "monet",
        "renoir",
        "picasso",
        "ancient egypt",
        "greek sculpture",
        "roman sculpture",
        "american painting",
        "european painting",
        "samurai armor",
        "medieval armor",
        "musical instrument",
        "japanese screen",
        "chinese ceramics",
        "impressionism",
        "met highlights",
    ]

    def __init__(
        self,
        db_path: str = "museum_guide.db",
        images_dir: str = "images",
        timeout: int = 20,
        max_retries: int = 3,
        request_delay: float = 0.10,
    ) -> None:
        self.db_path = Path(db_path)
        self.images_dir = Path(images_dir)
        self.timeout = timeout
        self.max_retries = max_retries
        self.request_delay = request_delay

        self.images_dir.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(self.db_path)
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": "Lensa-MetDataPipeline/1.0"})

        self.stats: Dict[str, int] = {
            "candidates_checked": 0,
            "saved": 0,
            "images_downloaded": 0,
            "api_errors": 0,
            "fetch_failed": 0,
            "db_failed": 0,
            "download_failed": 0,
            "missing_image": 0,
        }

        self._setup_database()

    def _setup_database(self) -> None:
        """
        Create a minimal artworks table if it does not exist.
        The insert logic only touches required fields so this remains compatible
        with richer schemas.
        """
        cursor = self.conn.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS artworks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                met_object_id INTEGER UNIQUE,
                title TEXT NOT NULL,
                artist TEXT,
                date TEXT,
                medium TEXT,
                department TEXT,
                image_url TEXT
            )
            """
        )
        self.conn.commit()

    def _get_json(
        self, endpoint: str, params: Optional[Dict[str, str]] = None
    ) -> Optional[Dict]:
        url = f"{self.BASE_URL}/{endpoint.lstrip('/')}"

        for attempt in range(1, self.max_retries + 1):
            try:
                response = self.session.get(url, params=params, timeout=self.timeout)
                response.raise_for_status()
                return response.json()
            except (requests.RequestException, ValueError):
                if attempt == self.max_retries:
                    self.stats["api_errors"] += 1
                    return None
                time.sleep(0.5 * attempt)
        return None

    def _collect_candidate_ids(self, target_count: int) -> List[int]:
        """
        Build a larger candidate pool so we can still finish with 100 items
        even if some records fail.
        """
        # Keep a moderate overflow pool to absorb failures without over-fetching.
        desired_pool = max(target_count * 2, target_count + 60)
        candidate_ids: List[int] = []
        seen = set()

        for query in self.HIGHLIGHT_QUERIES:
            data = self._get_json(
                "search",
                params={
                    "q": query,
                    "hasImages": "true",
                    "isHighlight": "true",
                },
            )
            ids = (data or {}).get("objectIDs") or []
            for object_id in ids:
                if object_id not in seen:
                    seen.add(object_id)
                    candidate_ids.append(object_id)
                    if len(candidate_ids) >= desired_pool:
                        return candidate_ids

            time.sleep(self.request_delay)

        # Fallback broad highlight terms.
        for query in ("art", "painting", "sculpture", "portrait"):
            data = self._get_json(
                "search",
                params={
                    "q": query,
                    "hasImages": "true",
                    "isHighlight": "true",
                },
            )
            ids = (data or {}).get("objectIDs") or []
            for object_id in ids:
                if object_id not in seen:
                    seen.add(object_id)
                    candidate_ids.append(object_id)
                    if len(candidate_ids) >= desired_pool:
                        return candidate_ids

            time.sleep(self.request_delay)

        # Final fallback if highlight pool is not enough.
        data = self._get_json("objects")
        all_ids = (data or {}).get("objectIDs") or []
        for object_id in all_ids:
            if object_id not in seen:
                seen.add(object_id)
                candidate_ids.append(object_id)
                if len(candidate_ids) >= desired_pool:
                    break

        return candidate_ids

    def _fetch_object(self, object_id: int) -> Optional[Dict]:
        data = self._get_json(f"objects/{object_id}")
        if not data or not data.get("objectID"):
            return None
        return data

    def _save_artwork(self, artwork: Dict) -> bool:
        met_object_id = artwork.get("objectID")
        title = artwork.get("title") or "Untitled"
        artist = (
            artwork.get("artistDisplayName")
            or artwork.get("artistAlphaSort")
            or "Unknown"
        )
        date = artwork.get("objectDate") or ""
        medium = artwork.get("medium") or ""
        department = artwork.get("department") or ""
        image_url = artwork.get("primaryImage") or artwork.get("primaryImageSmall") or ""

        if not met_object_id:
            return False

        try:
            cursor = self.conn.cursor()

            cursor.execute(
                """
                INSERT OR IGNORE INTO artworks (
                    met_object_id, title, artist, date, medium, department, image_url
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (met_object_id, title, artist, date, medium, department, image_url),
            )

            cursor.execute(
                """
                UPDATE artworks
                SET title = ?, artist = ?, date = ?, medium = ?, department = ?, image_url = ?
                WHERE met_object_id = ?
                """,
                (title, artist, date, medium, department, image_url, met_object_id),
            )

            self.conn.commit()
            return True
        except sqlite3.Error:
            return False

    @staticmethod
    def _image_extension(image_url: str) -> str:
        suffix = Path(urlparse(image_url).path).suffix.lower()
        if suffix in {".jpg", ".jpeg", ".png", ".webp"}:
            return suffix
        return ".jpg"

    def _download_image(self, object_id: int, image_url: str) -> bool:
        if not image_url:
            return False

        image_path = self.images_dir / f"{object_id}{self._image_extension(image_url)}"
        if image_path.exists():
            return True

        for attempt in range(1, self.max_retries + 1):
            try:
                with self.session.get(image_url, stream=True, timeout=self.timeout) as response:
                    response.raise_for_status()
                    with image_path.open("wb") as file_handle:
                        for chunk in response.iter_content(chunk_size=8192):
                            if chunk:
                                file_handle.write(chunk)
                return True
            except requests.RequestException:
                if image_path.exists():
                    image_path.unlink(missing_ok=True)
                if attempt == self.max_retries:
                    return False
                time.sleep(0.5 * attempt)

        return False

    def run(self, target_count: int = 100) -> None:
        print(f"Connecting to The Met API: {self.BASE_URL}")
        print(f"Database: {self.db_path.resolve()}")
        print(f"Images folder: {self.images_dir.resolve()}")
        print(f"Target artworks: {target_count}")

        candidate_ids = self._collect_candidate_ids(target_count)
        if not candidate_ids:
            print("No candidate IDs found. Exiting.")
            return

        print(f"Candidate pool collected: {len(candidate_ids)} IDs")

        progress = tqdm(total=target_count, desc="Saving artworks", unit="artwork")

        for object_id in candidate_ids:
            if self.stats["saved"] >= target_count:
                break

            self.stats["candidates_checked"] += 1
            artwork = self._fetch_object(object_id)
            if not artwork:
                self.stats["fetch_failed"] += 1
                continue

            image_url = artwork.get("primaryImage") or artwork.get("primaryImageSmall")
            if not image_url:
                self.stats["missing_image"] += 1
                continue

            if not self._save_artwork(artwork):
                self.stats["db_failed"] += 1
                continue

            self.stats["saved"] += 1
            progress.update(1)

            if self._download_image(object_id, image_url):
                self.stats["images_downloaded"] += 1
            else:
                self.stats["download_failed"] += 1

            time.sleep(self.request_delay)

        progress.close()
        self._print_summary(target_count)

    def _print_summary(self, target_count: int) -> None:
        cursor = self.conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM artworks")
        total_in_db = cursor.fetchone()[0]

        print("\n" + "=" * 56)
        print("Pipeline summary")
        print("=" * 56)
        print(f"Target requested           : {target_count}")
        print(f"Candidates checked         : {self.stats['candidates_checked']}")
        print(f"Saved to SQLite            : {self.stats['saved']}")
        print(f"Images downloaded          : {self.stats['images_downloaded']}")
        print(f"Failed object fetches      : {self.stats['fetch_failed']}")
        print(f"Missing image records      : {self.stats['missing_image']}")
        print(f"Database save failures     : {self.stats['db_failed']}")
        print(f"Image download failures    : {self.stats['download_failed']}")
        print(f"API call failures          : {self.stats['api_errors']}")
        print(f"Total rows in artworks tbl : {total_in_db}")
        print("=" * 56)

        if self.stats["saved"] < target_count:
            print(
                f"Warning: saved {self.stats['saved']} artworks, "
                f"which is below the requested {target_count}."
            )

    def close(self) -> None:
        self.session.close()
        self.conn.close()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Fetch famous Met artworks into SQLite.")
    parser.add_argument("--db-path", default="museum_guide.db", help="SQLite database file path")
    parser.add_argument("--images-dir", default="images", help="Directory to save images")
    parser.add_argument("--limit", type=int, default=100, help="Number of artworks to save")
    parser.add_argument(
        "--delay",
        type=float,
        default=0.10,
        help="Delay between object requests in seconds",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    pipeline = MetDataPipeline(
        db_path=args.db_path,
        images_dir=args.images_dir,
        request_delay=max(args.delay, 0.0),
    )
    try:
        pipeline.run(target_count=max(args.limit, 1))
    finally:
        pipeline.close()


if __name__ == "__main__":
    main()
