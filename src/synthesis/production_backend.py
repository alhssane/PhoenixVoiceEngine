from __future__ import annotations

import json
import os
import shlex
import subprocess
from pathlib import Path
from typing import Any

from src.analysis.arabic_phoneme_engine import ArabicPhonemeEngine
from src.synthesis.synthesis_backend import SynthesisBackend, SynthesisRequest, SynthesisResult


class ProductionSingingBackend(SynthesisBackend):
    """Production bridge for a real Arabic singing model.

    The model remains an external executable so Phoenix does not hard-code a
    fragile framework version. The adapter writes a complete request manifest,
    including Arabic phonemes and preservation controls, then validates the
    generated WAV before returning success.

    Environment variable:
      PHOENIX_PRODUCTION_SYNTH_COMMAND

    Supported template tokens:
      {request_json}, {reference_audio}, {melody_audio}, {output_audio},
      {reference_lyrics}, {target_lyrics}, {target_phonemes}, {language}
    """

    name = "production"
    VERSION = "1.0.0"

    def __init__(self, command: str | None = None) -> None:
        self.command = (
            command
            if command is not None
            else os.getenv("PHOENIX_PRODUCTION_SYNTH_COMMAND", "").strip()
        )
        self.phonemizer = ArabicPhonemeEngine()

    def supports(self, language: str) -> bool:
        return language.lower() == "ar" and bool(self.command)

    def synthesize(self, request: SynthesisRequest) -> SynthesisResult:
        if request.language.lower() != "ar":
            raise ValueError("ProductionSingingBackend currently supports Arabic only")
        if not self.command:
            raise RuntimeError(
                "PHOENIX_PRODUCTION_SYNTH_COMMAND is not configured; "
                "a real singing model must be installed before synthesis."
            )
        if not request.reference_audio.is_file():
            raise FileNotFoundError(request.reference_audio)
        if not request.melody_audio.is_file():
            raise FileNotFoundError(request.melody_audio)
        if not request.target_lyrics.strip():
            raise ValueError("Target lyrics cannot be empty")

        phonemes = self.phonemizer.phonemize(request.target_lyrics)
        request.output_audio.parent.mkdir(parents=True, exist_ok=True)
        manifest_path = request.output_audio.with_suffix(".request.json")
        manifest: dict[str, Any] = {
            "schema_version": "1.0",
            "backend": self.name,
            "language": "ar",
            "reference_audio": str(request.reference_audio),
            "melody_audio": str(request.melody_audio),
            "reference_lyrics": request.reference_lyrics,
            "target_lyrics": phonemes.text,
            "target_phonemes": phonemes.phonemes,
            "output_audio": str(request.output_audio),
            "preserve_style": request.preserve_style,
            "preserve_melody": request.preserve_melody,
        }
        manifest_path.write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
        )

        values = {
            "request_json": str(manifest_path),
            "reference_audio": str(request.reference_audio),
            "melody_audio": str(request.melody_audio),
            "output_audio": str(request.output_audio),
            "reference_lyrics": request.reference_lyrics,
            "target_lyrics": phonemes.text,
            "target_phonemes": phonemes.phonemes,
            "language": "ar",
        }
        command = self.command.format(**values)
        completed = subprocess.run(
            shlex.split(command, posix=os.name != "nt"),
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        if completed.returncode != 0:
            raise RuntimeError(
                "Production singing backend failed.\n"
                f"stdout:\n{completed.stdout[-8000:]}\n"
                f"stderr:\n{completed.stderr[-8000:]}"
            )
        if not request.output_audio.is_file() or request.output_audio.stat().st_size < 1024:
            raise RuntimeError(
                "Production backend finished without a valid output WAV: "
                f"{request.output_audio}"
            )

        return SynthesisResult(
            output_audio=request.output_audio,
            backend=self.name,
            metadata={
                "request_manifest": str(manifest_path),
                "phonemes": phonemes.phonemes,
                "stdout": completed.stdout[-4000:],
                "stderr": completed.stderr[-4000:],
            },
        )
