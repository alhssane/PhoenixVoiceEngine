from __future__ import annotations

import os
import shlex
import subprocess
from pathlib import Path

from src.synthesis.synthesis_backend import SynthesisBackend, SynthesisRequest, SynthesisResult


class HybridSingingBackend(SynthesisBackend):
    """Two-stage singing synthesis: melody/lyrics SVS, then target-voice conversion.

    Configure PHOENIX_SVS_COMMAND and PHOENIX_VC_COMMAND as command templates.
    SVS tokens: {reference_audio}, {melody_audio}, {reference_lyrics},
    {target_lyrics}, {svs_output_audio}, {language}.
    VC tokens: {reference_audio}, {input_audio}, {output_audio}, {language}.

    This keeps the model-specific CLI out of Phoenix while allowing the final
    system to combine an expressive singing model with an artist voice model.
    """

    name = "hybrid_svs_voice_conversion"

    def __init__(self, svs_command: str | None = None, vc_command: str | None = None) -> None:
        self.svs_command = (svs_command or os.getenv("PHOENIX_SVS_COMMAND", "")).strip()
        self.vc_command = (vc_command or os.getenv("PHOENIX_VC_COMMAND", "")).strip()

    def supports(self, language: str) -> bool:
        return language == "ar" and bool(self.svs_command) and bool(self.vc_command)

    @staticmethod
    def _run(command: str, values: dict[str, str]) -> subprocess.CompletedProcess[str]:
        expanded = command.format(**values)
        return subprocess.run(
            shlex.split(expanded, posix=os.name != "nt"),
            check=False,
            capture_output=True,
            text=True,
        )

    def synthesize(self, request: SynthesisRequest) -> SynthesisResult:
        if not self.supports(request.language):
            raise RuntimeError(
                "Hybrid Arabic backend requires PHOENIX_SVS_COMMAND and "
                "PHOENIX_VC_COMMAND."
            )

        request.output_audio.parent.mkdir(parents=True, exist_ok=True)
        svs_output = request.output_audio.with_name(request.output_audio.stem + ".svs.wav")
        svs = self._run(
            self.svs_command,
            {
                "reference_audio": str(request.reference_audio),
                "melody_audio": str(request.melody_audio),
                "reference_lyrics": request.reference_lyrics,
                "target_lyrics": request.target_lyrics,
                "svs_output_audio": str(svs_output),
                "language": request.language,
            },
        )
        if svs.returncode != 0 or not svs_output.is_file():
            raise RuntimeError(
                "SVS stage failed or did not create its output.\n"
                f"stdout:\n{svs.stdout}\n\nstderr:\n{svs.stderr}"
            )

        vc = self._run(
            self.vc_command,
            {
                "reference_audio": str(request.reference_audio),
                "input_audio": str(svs_output),
                "output_audio": str(request.output_audio),
                "language": request.language,
            },
        )
        if vc.returncode != 0 or not request.output_audio.is_file():
            raise RuntimeError(
                "Voice-conversion stage failed or did not create its output.\n"
                f"stdout:\n{vc.stdout}\n\nstderr:\n{vc.stderr}"
            )

        return SynthesisResult(
            output_audio=request.output_audio,
            backend=self.name,
            metadata={
                "svs_output": str(svs_output),
                "svs_stdout": svs.stdout[-4000:],
                "svs_stderr": svs.stderr[-4000:],
                "vc_stdout": vc.stdout[-4000:],
                "vc_stderr": vc.stderr[-4000:],
            },
        )
