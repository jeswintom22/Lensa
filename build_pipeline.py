"""Run Lensa data, feature, and audio generation pipelines in one command."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from typing import Dict

from artwork_recognition import ArtworkRecognitionEngine
from audio_generator import AudioNarrationGenerator
from met_data_pipeline import MetDataPipeline


DEFAULT_LIMIT = 100
DEFAULT_DB_PATH = "museum_guide.db"
DEFAULT_IMAGES_DIR = "images"
DEFAULT_AUDIO_DIR = "audio"
TABLE_WIDTH = 96


class PipelineExecutionError(RuntimeError):
    """Raised when one pipeline step fails and execution should stop."""


@dataclass
class StepSummary:
    """Structured result metadata for one pipeline step."""

    step: str
    status: str
    metrics: Dict[str, int]


class PipelineBuilder:
    """Orchestrate all pipeline steps and produce a terminal summary."""

    def __init__(
        self,
        db_path: str = DEFAULT_DB_PATH,
        images_dir: str = DEFAULT_IMAGES_DIR,
        audio_dir: str = DEFAULT_AUDIO_DIR,
        limit: int = DEFAULT_LIMIT,
    ) -> None:
        """Store execution parameters for a full build run."""
        self.db_path = db_path
        self.images_dir = images_dir
        self.audio_dir = audio_dir
        self.limit = max(int(limit), 1)

    def run(
        self,
        skip_data: bool = False,
        skip_features: bool = False,
        skip_audio: bool = False,
    ) -> Dict[str, StepSummary]:
        """Execute selected pipeline steps in required order."""
        summaries: Dict[str, StepSummary] = {}

        if skip_data:
            summaries["data"] = StepSummary(step="Data Pipeline", status="SKIPPED", metrics={})
        else:
            summaries["data"] = self._run_data_pipeline()

        if skip_features:
            summaries["features"] = StepSummary(
                step="Feature Extraction",
                status="SKIPPED",
                metrics={},
            )
        else:
            summaries["features"] = self._run_feature_pipeline()

        if skip_audio:
            summaries["audio"] = StepSummary(
                step="Audio Generation",
                status="SKIPPED",
                metrics={},
            )
        else:
            summaries["audio"] = self._run_audio_pipeline()

        self._print_summary_table(summaries=summaries)
        return summaries

    def _run_data_pipeline(self) -> StepSummary:
        """Execute metadata + image ingestion step and return metrics."""
        pipeline = MetDataPipeline(
            db_path=self.db_path,
            images_dir=self.images_dir,
        )
        try:
            pipeline.run(target_count=self.limit)
            return StepSummary(
                step="Data Pipeline",
                status="OK",
                metrics=dict(pipeline.stats),
            )
        except Exception as exc:  # pragma: no cover - defensive runtime boundary
            raise PipelineExecutionError(f"Data pipeline failed: {exc}") from exc
        finally:
            pipeline.close()

    def _run_feature_pipeline(self) -> StepSummary:
        """Execute ORB feature extraction step and return metrics."""
        engine = ArtworkRecognitionEngine(
            db_path=self.db_path,
            images_dir=self.images_dir,
        )
        try:
            stats = engine.build_feature_database()
            return StepSummary(step="Feature Extraction", status="OK", metrics=stats)
        except Exception as exc:  # pragma: no cover - defensive runtime boundary
            raise PipelineExecutionError(f"Feature extraction failed: {exc}") from exc
        finally:
            engine.close()

    def _run_audio_pipeline(self) -> StepSummary:
        """Execute local narration generation step and return metrics."""
        generator = AudioNarrationGenerator(
            db_path=self.db_path,
            audio_dir=self.audio_dir,
        )
        try:
            stats = generator.generate_audio_for_all(limit=self.limit)
            return StepSummary(step="Audio Generation", status="OK", metrics=stats)
        except Exception as exc:  # pragma: no cover - defensive runtime boundary
            raise PipelineExecutionError(f"Audio generation failed: {exc}") from exc
        finally:
            generator.close()

    @staticmethod
    def _format_metrics(metrics: Dict[str, int]) -> str:
        """Render compact key=value metrics text for terminal output."""
        if not metrics:
            return "-"
        return ", ".join(f"{key}={value}" for key, value in metrics.items())

    def _print_summary_table(self, summaries: Dict[str, StepSummary]) -> None:
        """Print end-of-run summary table for all step results."""
        print("\n" + "=" * TABLE_WIDTH)
        print("Lensa Build Pipeline Summary")
        print("=" * TABLE_WIDTH)
        print(f"{'Step':24} | {'Status':8} | Metrics")
        print("-" * TABLE_WIDTH)
        for key in ("data", "features", "audio"):
            summary = summaries.get(key)
            if summary is None:
                continue
            metrics_text = self._format_metrics(summary.metrics)
            print(f"{summary.step:24} | {summary.status:8} | {metrics_text}")
        print("=" * TABLE_WIDTH)


def parse_args() -> argparse.Namespace:
    """Parse CLI flags for selecting and configuring build pipeline steps."""
    parser = argparse.ArgumentParser(description="Run complete Lensa content build pipeline.")
    parser.add_argument("--limit", type=int, default=DEFAULT_LIMIT, help="Artwork processing limit")
    parser.add_argument("--db-path", default=DEFAULT_DB_PATH, help="SQLite database path")
    parser.add_argument("--images-dir", default=DEFAULT_IMAGES_DIR, help="Artwork images directory")
    parser.add_argument("--audio-dir", default=DEFAULT_AUDIO_DIR, help="Narration audio directory")
    parser.add_argument(
        "--skip-data",
        action="store_true",
        help="Skip Met API data + image ingestion step",
    )
    parser.add_argument(
        "--skip-features",
        action="store_true",
        help="Skip ORB feature extraction step",
    )
    parser.add_argument(
        "--skip-audio",
        action="store_true",
        help="Skip narration MP3 generation step",
    )
    return parser.parse_args()


def main() -> None:
    """Run CLI entrypoint and terminate early if any step fails."""
    args = parse_args()
    builder = PipelineBuilder(
        db_path=args.db_path,
        images_dir=args.images_dir,
        audio_dir=args.audio_dir,
        limit=args.limit,
    )
    try:
        builder.run(
            skip_data=args.skip_data,
            skip_features=args.skip_features,
            skip_audio=args.skip_audio,
        )
    except PipelineExecutionError as exc:
        print("\nBuild pipeline aborted.")
        print(str(exc))
        raise SystemExit(1) from exc


if __name__ == "__main__":
    main()
