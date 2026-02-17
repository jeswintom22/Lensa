"""
Artwork recognition pipeline for Lensa.

Features:
1. Load artwork images from ./images.
2. Extract ORB descriptors with OpenCV.
3. Save descriptors as SQLite BLOBs.
4. Accept query image path input.
5. Compare query descriptors against all stored descriptors.
6. Return best matching artwork + confidence.
7. Return None when confidence is below threshold.
"""

from __future__ import annotations

import argparse
import pickle
import sqlite3
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import cv2
import numpy as np
from tqdm import tqdm


class ArtworkRecognitionEngine:
    def __init__(
        self,
        db_path: str = "museum_guide.db",
        images_dir: str = "images",
        nfeatures: int = 2000,
    ) -> None:
        self.db_path = Path(db_path)
        self.images_dir = Path(images_dir)
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
        self.orb = cv2.ORB_create(nfeatures=nfeatures)
        self.matcher = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=False)
        self._ensure_tables()

    def _ensure_tables(self) -> None:
        cursor = self.conn.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS artwork_features (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                artwork_id INTEGER NOT NULL,
                feature_descriptor BLOB NOT NULL,
                feature_type TEXT DEFAULT 'orb',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (artwork_id) REFERENCES artworks(id)
            )
            """
        )
        self.conn.commit()

    @staticmethod
    def _parse_met_object_id_from_filename(image_path: Path) -> Optional[int]:
        stem = image_path.stem.strip()
        if stem.isdigit():
            return int(stem)
        return None

    def _extract_orb_descriptors(self, image: np.ndarray) -> Optional[np.ndarray]:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        _keypoints, descriptors = self.orb.detectAndCompute(gray, None)
        return descriptors

    def _load_artwork_index(self) -> Dict[int, sqlite3.Row]:
        cursor = self.conn.cursor()
        cursor.execute("SELECT id, met_object_id, title FROM artworks")
        rows = cursor.fetchall()
        index: Dict[int, sqlite3.Row] = {}
        for row in rows:
            met_id = row["met_object_id"]
            if met_id is not None:
                index[int(met_id)] = row
        return index

    def build_feature_database(self) -> Dict[str, int]:
        """
        Load all images from images_dir, extract ORB descriptors,
        and save descriptors as BLOBs in SQLite.
        """
        if not self.images_dir.exists():
            raise FileNotFoundError(f"Images directory not found: {self.images_dir}")

        artwork_index = self._load_artwork_index()
        image_paths: List[Path] = []
        for ext in ("*.jpg", "*.jpeg", "*.png", "*.webp", "*.bmp"):
            image_paths.extend(self.images_dir.glob(ext))

        image_paths = sorted(image_paths)

        stats = {
            "images_found": len(image_paths),
            "saved_features": 0,
            "skipped_no_met_id": 0,
            "skipped_not_in_db": 0,
            "skipped_load_error": 0,
            "skipped_no_features": 0,
        }

        cursor = self.conn.cursor()

        for image_path in tqdm(image_paths, desc="Extracting ORB", unit="image"):
            met_object_id = self._parse_met_object_id_from_filename(image_path)
            if met_object_id is None:
                stats["skipped_no_met_id"] += 1
                continue

            artwork = artwork_index.get(met_object_id)
            if artwork is None:
                stats["skipped_not_in_db"] += 1
                continue

            image = cv2.imread(str(image_path))
            if image is None:
                stats["skipped_load_error"] += 1
                continue

            descriptors = self._extract_orb_descriptors(image)
            if descriptors is None or len(descriptors) == 0:
                stats["skipped_no_features"] += 1
                continue

            descriptor_blob = sqlite3.Binary(
                pickle.dumps(descriptors, protocol=pickle.HIGHEST_PROTOCOL)
            )

            cursor.execute(
                "DELETE FROM artwork_features WHERE artwork_id = ? AND feature_type = 'orb'",
                (artwork["id"],),
            )
            cursor.execute(
                """
                INSERT INTO artwork_features (artwork_id, feature_descriptor, feature_type)
                VALUES (?, ?, 'orb')
                """,
                (artwork["id"], descriptor_blob),
            )
            stats["saved_features"] += 1

        self.conn.commit()
        return stats

    def _compute_match_confidence(
        self,
        query_desc: np.ndarray,
        ref_desc: np.ndarray,
        ratio_test: float,
    ) -> Tuple[int, float]:
        """
        Returns: (good_match_count, confidence_score[0..1+])
        """
        try:
            knn_matches = self.matcher.knnMatch(query_desc, ref_desc, k=2)
        except cv2.error:
            return 0, 0.0

        good_matches = []
        for pair in knn_matches:
            if len(pair) < 2:
                continue
            m, n = pair
            if n.distance == 0 and m.distance == 0:
                good_matches.append(m)
            elif m.distance < ratio_test * n.distance:
                good_matches.append(m)

        good_count = len(good_matches)
        if good_count == 0:
            return 0, 0.0

        denominator = max(min(len(query_desc), len(ref_desc)), 1)
        match_ratio = good_count / denominator

        mean_distance = float(np.mean([m.distance for m in good_matches]))
        distance_quality = max(0.0, 1.0 - (mean_distance / 256.0))

        confidence = (0.7 * match_ratio) + (0.3 * distance_quality)
        return good_count, confidence

    def _get_artwork_details(self, artwork_id: int) -> Dict[str, object]:
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM artworks WHERE id = ?", (artwork_id,))
        row = cursor.fetchone()
        if row is None:
            return {"id": artwork_id}
        return dict(row)

    def recognize_from_path(
        self,
        query_image_path: str,
        confidence_threshold: float = 0.18,
        ratio_test: float = 0.75,
        min_good_matches: int = 12,
    ) -> Optional[Dict[str, object]]:
        """
        Compare query image against all stored ORB descriptors.
        Returns best artwork match + confidence, or None if below threshold.
        """
        query_path = Path(query_image_path)
        image = cv2.imread(str(query_path))
        if image is None:
            raise FileNotFoundError(f"Cannot read query image: {query_path}")

        query_desc = self._extract_orb_descriptors(image)
        if query_desc is None or len(query_desc) == 0:
            return None

        cursor = self.conn.cursor()
        cursor.execute(
            """
            SELECT artwork_id, feature_descriptor
            FROM artwork_features
            WHERE feature_type = 'orb'
            """
        )
        rows = cursor.fetchall()
        if not rows:
            return None

        best_artwork_id: Optional[int] = None
        best_confidence = 0.0
        best_good_matches = 0

        for row in rows:
            ref_desc = pickle.loads(row["feature_descriptor"])
            if ref_desc is None or len(ref_desc) == 0:
                continue

            good_matches, confidence = self._compute_match_confidence(
                query_desc=query_desc,
                ref_desc=ref_desc,
                ratio_test=ratio_test,
            )

            if confidence > best_confidence:
                best_confidence = confidence
                best_good_matches = good_matches
                best_artwork_id = int(row["artwork_id"])

        if best_artwork_id is None:
            return None

        if best_confidence < confidence_threshold or best_good_matches < min_good_matches:
            return None

        artwork = self._get_artwork_details(best_artwork_id)
        return {
            "artwork": artwork,
            "confidence": round(float(best_confidence), 4),
            "good_matches": int(best_good_matches),
            "query_features": int(len(query_desc)),
        }

    def close(self) -> None:
        self.conn.close()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build and run ORB artwork recognition.")
    parser.add_argument("--db-path", default="museum_guide.db", help="Path to SQLite DB")
    parser.add_argument("--images-dir", default="images", help="Directory with artwork images")
    parser.add_argument(
        "--build",
        action="store_true",
        help="Extract ORB descriptors from /images and save into SQLite",
    )
    parser.add_argument(
        "--query",
        help="Query image path to recognize against stored artwork descriptors",
    )
    parser.add_argument(
        "--confidence-threshold",
        type=float,
        default=0.18,
        help="Return None below this confidence",
    )
    parser.add_argument(
        "--ratio-test",
        type=float,
        default=0.75,
        help="Lowe ratio threshold for filtering matches",
    )
    parser.add_argument(
        "--min-good-matches",
        type=int,
        default=12,
        help="Minimum good matches required before returning a result",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    engine = ArtworkRecognitionEngine(db_path=args.db_path, images_dir=args.images_dir)
    try:
        if not args.build and not args.query:
            # Default behavior for first run: build feature DB.
            args.build = True

        if args.build:
            stats = engine.build_feature_database()
            print("Feature extraction summary:")
            for key, value in stats.items():
                print(f"  {key}: {value}")

        if args.query:
            result = engine.recognize_from_path(
                query_image_path=args.query,
                confidence_threshold=args.confidence_threshold,
                ratio_test=args.ratio_test,
                min_good_matches=args.min_good_matches,
            )
            if result is None:
                print("Recognition result: None (below threshold or no reliable match)")
            else:
                artwork = result["artwork"]
                title = artwork.get("title", "Unknown title")
                met_id = artwork.get("met_object_id", "Unknown")
                print("Recognition result:")
                print(f"  title: {title}")
                print(f"  met_object_id: {met_id}")
                print(f"  confidence: {result['confidence']}")
                print(f"  good_matches: {result['good_matches']}")
    finally:
        engine.close()


if __name__ == "__main__":
    main()
