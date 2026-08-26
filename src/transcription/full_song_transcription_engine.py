from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from faster_whisper import WhisperModel


class FullSongTranscriptionEngine:
    """Arabic-first lyric transcription with portable model/output paths."""

    VERSION = "2.0.0"

    def __init__(
        self,
        model_path: str | Path | None = None,
        device: str | None = None,
        compute_type: str | None = None,
    ) -> None:
        self.model_path = str(
            model_path or os.getenv("PHOENIX_WHISPER_MODEL", "large-v3")
        )
        self.device = device or os.getenv("PHOENIX_WHISPER_DEVICE", "cpu")
        self.compute_type = compute_type or os.getenv(
            "PHOENIX_WHISPER_COMPUTE_TYPE", "int8"
        )
        self._model: WhisperModel | None = None

    def _get_model(self) -> WhisperModel:
        if self._model is None:
            self._model = WhisperModel(
                self.model_path,
                device=self.device,
                compute_type=self.compute_type,
            )
        return self._model

    def transcribe(
        self,
        audio_path: str | Path,
        output_path: str | Path | None = None,
        language: str = "ar",
    ) -> dict[str, Any]:
        audio_path = Path(audio_path)
        if not audio_path.is_file():
            raise FileNotFoundError(f"Audio file not found: {audio_path}")

        model = self._get_model()
        segments, info = model.transcribe(
            str(audio_path),
            language=language,
            word_timestamps=True,
            vad_filter=True,
            condition_on_previous_text=True,
        )

        words: list[dict[str, Any]] = []
        for segment in segments:
            for word in segment.words or []:
                text = (word.word or "").strip()
                if not text:
                    continue
                start = round(float(word.start), 3)
                end = round(float(word.end), 3)
                words.append(
                    {
                        "word": text,
                        "start": start,
                        "end": end,
                        "duration": round(max(0.0, end - start), 3),
                    }
                )

        destination = Path(output_path) if output_path else (
            audio_path.parent / f"{audio_path.stem}.words.json"
        )
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(
            json.dumps(words, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

        return {
            "words": len(words),
            "language": getattr(info, "language", language),
            "language_probability": round(
                float(getattr(info, "language_probability", 0.0)), 4
            ),
            "duration": round(float(info.duration), 3),
            "output": str(destination),
        }
