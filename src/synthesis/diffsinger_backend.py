from __future__ import annotations

import os
import shlex
import subprocess
from typing import Any

from src.synthesis.synthesis_backend import SynthesisBackend, SynthesisRequest, SynthesisResult


class DiffSingerBackend(SynthesisBackend):
    """Production adapter for an externally installed DiffSinger/OpenVPI runner.

    Phoenix owns alignment, Arabic G2P, pitch/expression analysis and
    validation; the configured SVS model owns neural waveform generation.
    """

    name = "diffsinger"

    def __init__(self, command: str | None = None) -> None:
        self.command = command or os.getenv("PHOENIX_DIFFSINGER_COMMAND", "").strip()

    def supports(self, language: str) -> bool:
        return language.lower().startswith("ar") and bool(self.command)

    def synthesize(self, request: SynthesisRequest) -> SynthesisResult:
        if not self.supports(request.language):
            raise RuntimeError(
                "PHOENIX_DIFFSINGER_COMMAND is not configured for Arabic synthesis."
            )
        request.output_audio.parent.mkdir(parents=True, exist_ok=True)
        values: dict[str, Any] = {
            "reference_audio": str(request.reference_audio),
            "melody_audio": str(request.melody_audio),
            "reference_lyrics": request.reference_lyrics,
            "target_lyrics": request.target_lyrics,
            "output_audio": str(request.output_audio),
            "language": request.language,
        }
        command = self.command.format(**values)
        completed = subprocess.run(
            shlex.split(command, posix=os.name != "nt"),
            check=False,
            capture_output=True,
            text=True,
        )
        if completed.returncode != 0:
            raise RuntimeError(
                "DiffSinger backend failed.\n"
                f"stdout:\n{completed.stdout[-4000:]}\n"
                f"stderr:\n{completed.stderr[-4000:]}"
            )
        if not request.output_audio.is_file():
            raise RuntimeError(
                f"DiffSinger completed without creating {request.output_audio}"
            )
        return SynthesisResult(
            output_audio=request.output_audio,
            backend=self.name,
            metadata={"stdout": completed.stdout[-4000:], "stderr": completed.stderr[-4000:]},
        )
