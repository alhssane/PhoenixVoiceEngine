from __future__ import annotations

import os
import shlex
import subprocess
from pathlib import Path

from src.synthesis.synthesis_backend import (
    SynthesisBackend,
    SynthesisRequest,
    SynthesisResult,
)


class CommandSynthesisBackend(SynthesisBackend):
    """Run a configured external singing model without coupling Phoenix to it.

    Configure PHOENIX_SYNTH_COMMAND as a command template. Supported tokens:
    {reference_audio}, {melody_audio}, {reference_lyrics}, {target_lyrics},
    {output_audio}, {language}.
    """

    name = "command"

    def __init__(self, command: str | None = None) -> None:
        self.command = command or os.getenv("PHOENIX_SYNTH_COMMAND", "").strip()

    def supports(self, language: str) -> bool:
        return bool(self.command) and bool(language)

    def synthesize(self, request: SynthesisRequest) -> SynthesisResult:
        if not self.command:
            raise RuntimeError(
                "PHOENIX_SYNTH_COMMAND is not configured. "
                "Install/configure a singing backend before synthesis."
            )

        request.output_audio.parent.mkdir(parents=True, exist_ok=True)
        values = {
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
                "Synthesis backend failed.\n"
                f"stdout:\n{completed.stdout}\n"
                f"stderr:\n{completed.stderr}"
            )

        if not request.output_audio.is_file():
            raise RuntimeError(
                "Synthesis backend completed without creating the expected "
                f"output: {request.output_audio}"
            )

        return SynthesisResult(
            output_audio=request.output_audio,
            backend=self.name,
            metadata={
                "stdout": completed.stdout[-4000:],
                "stderr": completed.stderr[-4000:],
            },
        )
