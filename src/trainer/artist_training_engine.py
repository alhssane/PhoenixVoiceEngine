from __future__ import annotations

import json
from pathlib import Path

from src.analysis.real_note_extraction_engine import (
    RealNoteExtractionEngine,
)

from src.analysis.syllable_detection_engine import (
    SyllableDetectionEngine,
)

from src.voice.voice_dna_engine import (
    VoiceDNAEngine,
)


class ArtistTrainingEngine:

    VERSION = "1.0.0"

    def train(
        self,
        audio_path,
        words_path,
        output_path,
    ):

        audio_path = Path(audio_path)
        words_path = Path(words_path)
        output_path = Path(output_path)

        words = json.loads(
            words_path.read_text(
                encoding="utf-8",
            )
        )

        notes = (
            RealNoteExtractionEngine()
            .analyze(
                str(audio_path)
            )
        )

        syllables = (
            SyllableDetectionEngine()
            .analyze(
                str(audio_path)
            )
        )

        voice_profile = (
            VoiceDNAEngine()
            .build_profile(
                timbre=0.90,
                vibrato=0.85,
                expression=0.95,
                articulation=0.92,
            )
        )

        duration = max(
            item["end"]
            for item in words
        )

        profile = {
            "artist": "fareed",
            "audio_file": audio_path.name,
            "duration": round(
                duration,
                2,
            ),
            "word_count": len(
                words
            ),
            "syllable_count": len(
                syllables
            ),
            "maqam": (
                "hijaz_husayni"
            ),
            "note_distribution": (
                notes
            ),
            "voice_profile": (
                voice_profile
            ),
        }

        output_path.write_text(
            json.dumps(
                profile,
                ensure_ascii=False,
                indent=4,
            ),
            encoding="utf-8",
        )

        return profile