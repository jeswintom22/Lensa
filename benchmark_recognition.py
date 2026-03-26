"""Benchmark self-consistency of ORB recognition against local image filenames."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Dict, List, Optional

from tqdm import tqdm

from artwork_recognition import ArtworkRecognitionEngine


DEFAULT_DB_PATH = "museum_guide.db"
DEFAULT_IMAGES_DIR = "images"
SUPPORTED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".bmp"}


class RecognitionBenchmark:
    """Run local recognition on each source image and report match accuracy."""

    def __init__(self, db_path: str = DEFAULT_DB_PATH, images_dir: str = DEFAULT_IMAGES_DIR) -> None:
        """Initialize benchmark runner with DB and image directory paths."""
        self.db_path = db_path
        self.images_dir = Path(images_dir)

    def run(self) -> Dict[str, float]:
        """Execute benchmark and return aggregate metrics."""
        image_paths = self._load_image_paths()
        engine = ArtworkRecognitionEngine(db_path=self.db_path, images_dir=str(self.images_dir))

        total_tested = 0
        correct = 0
        incorrect = 0
        no_match = 0

        try:
            for image_path in tqdm(image_paths, desc="Benchmarking", unit="image"):
                expected_id = self._expected_met_id(image_path)
                if expected_id is None:
                    continue

                total_tested += 1
                try:
                    result = engine.recognize_from_path(str(image_path))
                except Exception:
                    no_match += 1
                    continue

                if result is None:
                    no_match += 1
                    continue

                recognized_id = self._recognized_met_id(result)
                if recognized_id == expected_id:
                    correct += 1
                else:
                    incorrect += 1
        finally:
            engine.close()

        accuracy = (correct / total_tested * 100.0) if total_tested > 0 else 0.0
        metrics: Dict[str, float] = {
            "total_tested": float(total_tested),
            "correct": float(correct),
            "incorrect": float(incorrect),
            "no_match": float(no_match),
            "accuracy_percent": accuracy,
        }
        self._print_report(metrics=metrics)
        return metrics

    def _load_image_paths(self) -> List[Path]:
        if not self.images_dir.exists():
            return []
        return sorted(
            path
            for path in self.images_dir.iterdir()
            if path.is_file() and path.suffix.lower() in SUPPORTED_EXTENSIONS
        )

    @staticmethod
    def _expected_met_id(image_path: Path) -> Optional[int]:
        stem = image_path.stem.strip()
        if stem.isdigit():
            return int(stem)
        return None

    @staticmethod
    def _recognized_met_id(result: Dict[str, object]) -> Optional[int]:
        artwork = result.get("artwork")
        if not isinstance(artwork, dict):
            return None
        value = artwork.get("met_object_id")
        if value is None:
            return None
        try:
            return int(value)
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _print_report(metrics: Dict[str, float]) -> None:
        print("\nRecognition Benchmark Summary")
        print("=" * 40)
        print(f"Total tested : {int(metrics['total_tested'])}")
        print(f"Correct      : {int(metrics['correct'])}")
        print(f"Incorrect    : {int(metrics['incorrect'])}")
        print(f"No-match     : {int(metrics['no_match'])}")
        print(f"Accuracy     : {metrics['accuracy_percent']:.2f}%")


def parse_args() -> argparse.Namespace:
    """Parse benchmark command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Benchmark recognition self-consistency against source images."
    )
    parser.add_argument("--images-dir", default=DEFAULT_IMAGES_DIR, help="Directory with images")
    parser.add_argument("--db-path", default=DEFAULT_DB_PATH, help="SQLite database path")
    return parser.parse_args()


def main() -> None:
    """Run benchmark from command line."""
    args = parse_args()
    benchmark = RecognitionBenchmark(db_path=args.db_path, images_dir=args.images_dir)
    benchmark.run()


if __name__ == "__main__":
    main()
