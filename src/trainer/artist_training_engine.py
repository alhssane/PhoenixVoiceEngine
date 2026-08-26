from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import soundfile as sf

from src.analysis.clean_vocal_signature_engine import CleanVocalSignatureEngine
from src.analysis.real_note_extraction_engine import RealNoteExtractionEngine
from src.analysis.syllable_detection_engine import SyllableDetectionEngine


class ArtistTrainingEngine:
    """Build a reproducible singer-analysis package from a clean vocal.

    The output is an analysis/profile package consumed by a synthesis backend.
    It deliberately does not fabricate artist names, maqam labels, or quality
    scores when the evidence is unavailable.
    """

    VERSION = "2.0.0"

    def train(
        self,
        audio_path: str | Path,
        words_path: str | Path,
        output_path: str | Path,
        artist_name: str = "unknown",
    ) -> dict[str, Any]:
        audio_path = Path(audio_path)
        words_path = Path(words_path)
        output_path = Path(output_path)

        if not audio_path.is_file():
            raise FileNotFoundError(f"Audio file not found: {audio_path}")
        if not words_path.is_file():
            raise FileNotFoundError(f"Words file not found: {words_path}")

        words = json.loads(words_path.read_text(encoding="utf-8"))
        if not isinstance(words, list):
            raise ValueError("Words file must contain a JSON list.")

        info = sf.info(str(audio_path))
        notes = RealNoteExtractionEngine().analyze(str(audio_path))
        syllables = SyllableDetectionEngine().analyze(str(audio_path))
        signature = CleanVocalSignatureEngine().analyze(str(audio_path))

        profile = {
            "schema_version": "2.0",
            "artist": artist_name.strip() or "unknown",
            "audio_file": audio_path.name,
            "duration": round(float(info.duration), 3),
            "sample_rate": int(info.samplerate),
            "channels": int(info.channels),
            "word_count": len(words),
            "syllable_count": len(syllables),
            "note_analysis": notes,
            "vocal_signature": signature,
            "lyrics": words,
            "maqam": None,
            "training_status": "ANALYSIS_READY",
            "synthesis_model": None,
        }

        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(
            json.dumps(profile, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        return profile
