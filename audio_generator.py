"""
Generate audio narrations for all artworks in SQLite.

This script:
1. Reads artworks from SQLite.
2. Builds a ~60-second narration in this format:
   Hook -> Context -> Key Feature -> Fun Fact -> Call to Action
3. Converts narration text to MP3 using gTTS.
4. Saves MP3 files in ./audio.
5. Updates artworks.audio_file_path in SQLite.
"""

from __future__ import annotations

import argparse
import re
import sqlite3
from datetime import date
from pathlib import Path
from typing import Dict, Iterable, List, Optional

try:
    from gtts import gTTS
except ImportError:
    gTTS = None
from tqdm import tqdm


def _clean_text(value: Optional[str], fallback: str = "") -> str:
    if value is None:
        return fallback
    text = str(value).strip()
    return text if text else fallback


def _first_year_from_text(text: str) -> Optional[int]:
    match = re.search(r"(1[0-9]{3}|20[0-9]{2})", text or "")
    if match:
        return int(match.group(1))
    return None


class AudioNarrationGenerator:
    def __init__(self, db_path: str = "museum_guide.db", audio_dir: str = "audio") -> None:
        self.db_path = Path(db_path)
        self.audio_dir = Path(audio_dir)
        self.audio_dir.mkdir(parents=True, exist_ok=True)

        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
        self._ensure_audio_column()

    def _ensure_audio_column(self) -> None:
        cursor = self.conn.cursor()
        cursor.execute("PRAGMA table_info(artworks)")
        column_names = {row[1] for row in cursor.fetchall()}
        if "audio_file_path" not in column_names:
            cursor.execute("ALTER TABLE artworks ADD COLUMN audio_file_path TEXT")
            self.conn.commit()

    def fetch_artworks(self, limit: Optional[int] = None) -> List[sqlite3.Row]:
        cursor = self.conn.cursor()
        query = """
            SELECT id, met_object_id, title, artist, date, medium, department
            FROM artworks
            ORDER BY id ASC
        """
        params: Iterable[object] = ()
        if limit is not None and limit > 0:
            query += " LIMIT ?"
            params = (int(limit),)
        cursor.execute(query, params)
        return cursor.fetchall()

    def generate_narration_script(self, artwork: sqlite3.Row, target_words: int = 125) -> str:
        """
        Build a narration with fixed section order:
        Hook -> Context -> Key Feature -> Fun Fact -> Call to Action
        """
        title = _clean_text(artwork["title"], "this artwork")
        artist = _clean_text(artwork["artist"], "an unknown artist")
        date_text = _clean_text(artwork["date"], "an unknown period")
        medium = _clean_text(artwork["medium"], "mixed media")
        department = _clean_text(artwork["department"], "the museum collection")

        hook = (
            f"You are standing in front of {title}, a work that draws attention almost immediately."
        )

        context = (
            f"It was created by {artist} around {date_text}, and it belongs to {department}. "
            f"The piece is made in {medium}, which gives it a distinctive visual presence."
        )

        key_feature = self._key_feature_section(title=title, medium=medium, department=department)
        fun_fact = self._fun_fact_section(artist=artist, date_text=date_text, department=department)
        cta = (
            "Take a few extra seconds, move slightly left and right, and notice how new details "
            "appear as your viewing angle changes."
        )

        sections = [hook, context, key_feature, fun_fact, cta]
        script = " ".join(sections)
        script = self._normalize_length(script=script, artwork=artwork, target_words=target_words)
        return script

    def _key_feature_section(self, title: str, medium: str, department: str) -> str:
        medium_lower = medium.lower()
        dept_lower = department.lower()

        if "oil" in medium_lower or "painting" in dept_lower:
            return (
                f"For a key feature, look at the brushwork in {title}: color, light, and texture are "
                "used to guide your eye through the composition."
            )
        if "marble" in medium_lower or "sculpture" in dept_lower:
            return (
                "For a key feature, focus on the carved surfaces and the transitions between smooth and "
                "sharp forms, which create depth even in still stone."
            )
        if "armor" in dept_lower or "arms" in dept_lower:
            return (
                "For a key feature, notice how decoration and protection work together, showing both "
                "craftsmanship and practical engineering."
            )
        if "egyptian" in dept_lower:
            return (
                "For a key feature, examine the symbolic forms and repeated motifs, which often carried "
                "religious or royal meaning in their original context."
            )
        return (
            "For a key feature, observe how shape, material, and detail are balanced to express the "
            "artist's intent clearly."
        )

    def _fun_fact_section(self, artist: str, date_text: str, department: str) -> str:
        artist_lower = artist.lower()
        dept_lower = department.lower()

        if "van gogh" in artist_lower:
            return (
                "Fun fact: Van Gogh produced an extraordinary number of works in a short period, and his "
                "technique turned visible brushstrokes into emotional storytelling."
            )
        if "vermeer" in artist_lower:
            return (
                "Fun fact: Vermeer left a relatively small body of paintings, which is one reason his "
                "works are studied so closely today."
            )
        if "rembrandt" in artist_lower:
            return (
                "Fun fact: Rembrandt repeatedly experimented with light and shadow, pushing portrait "
                "painting toward stronger psychological depth."
            )
        if "egyptian" in dept_lower:
            return (
                "Fun fact: Many Egyptian objects survived across millennia, preserving beliefs, rituals, "
                "and daily life details with remarkable continuity."
            )

        year = _first_year_from_text(date_text)
        if year is not None:
            years_old = max(date.today().year - year, 0)
            return (
                f"Fun fact: this work is about {years_old} years old, connecting viewers today with "
                "creative choices made in a very different historical moment."
            )

        return (
            "Fun fact: museum objects like this often reveal new stories when historians compare style, "
            "materials, and provenance records."
        )

    def _normalize_length(self, script: str, artwork: sqlite3.Row, target_words: int) -> str:
        """
        Keep script close to 60 seconds for TTS.
        Approximation: ~120-135 words for a one-minute narration.
        """
        min_words = max(110, target_words - 15)
        max_words = target_words + 10

        words = script.split()

        filler = (
            f"This artwork from {_clean_text(artwork['department'], 'the collection')} rewards "
            "slow looking, because subtle details become clearer over time."
        )

        while len(words) < min_words:
            words.extend(filler.split())

        if len(words) > max_words:
            words = words[:max_words]
            if words and not words[-1].endswith((".", "!", "?")):
                words[-1] = words[-1].rstrip(",;:") + "."

        return " ".join(words)

    def _audio_filename(self, artwork_id: int, met_object_id: Optional[int]) -> str:
        suffix = str(met_object_id) if met_object_id else str(artwork_id)
        return f"artwork_{suffix}.mp3"

    def generate_audio_for_all(
        self,
        lang: str = "en",
        limit: Optional[int] = None,
        overwrite: bool = False,
    ) -> Dict[str, int]:
        if gTTS is None:
            raise RuntimeError("gTTS is not installed. Run: pip install gTTS")

        artworks = self.fetch_artworks(limit=limit)
        cursor = self.conn.cursor()

        stats = {
            "artworks_read": len(artworks),
            "audio_generated": 0,
            "audio_skipped_existing": 0,
            "audio_failed": 0,
            "db_updated": 0,
        }

        for artwork in tqdm(artworks, desc="Generating audio", unit="artwork"):
            artwork_id = int(artwork["id"])
            met_object_id = artwork["met_object_id"]
            script = self.generate_narration_script(artwork)

            filename = self._audio_filename(artwork_id=artwork_id, met_object_id=met_object_id)
            output_path = self.audio_dir / filename
            relative_path = str(Path(self.audio_dir.name) / filename)

            if output_path.exists() and not overwrite:
                stats["audio_skipped_existing"] += 1
            else:
                try:
                    tts = gTTS(text=script, lang=lang, slow=False)
                    tts.save(str(output_path))
                    stats["audio_generated"] += 1
                except Exception:
                    stats["audio_failed"] += 1
                    continue

            cursor.execute(
                "UPDATE artworks SET audio_file_path = ? WHERE id = ?",
                (relative_path, artwork_id),
            )
            stats["db_updated"] += 1

        self.conn.commit()
        return stats

    def close(self) -> None:
        self.conn.close()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate MP3 narrations for artworks.")
    parser.add_argument("--db-path", default="museum_guide.db", help="Path to SQLite database")
    parser.add_argument("--audio-dir", default="audio", help="Directory where MP3 files are stored")
    parser.add_argument("--lang", default="en", help="gTTS language code")
    parser.add_argument("--limit", type=int, default=None, help="Optional limit for number of artworks")
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Regenerate MP3s even if files already exist",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    generator = AudioNarrationGenerator(db_path=args.db_path, audio_dir=args.audio_dir)
    try:
        stats = generator.generate_audio_for_all(
            lang=args.lang,
            limit=args.limit,
            overwrite=args.overwrite,
        )
        print("Audio generation summary:")
        for key, value in stats.items():
            print(f"  {key}: {value}")
        print(f"Audio folder: {Path(args.audio_dir).resolve()}")
    finally:
        generator.close()


if __name__ == "__main__":
    main()
