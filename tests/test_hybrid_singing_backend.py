from pathlib import Path

import pytest

from src.synthesis.hybrid_singing_backend import HybridSingingBackend
from src.synthesis.synthesis_backend import SynthesisRequest


def test_hybrid_requires_both_stages():
    assert not HybridSingingBackend(svs_command="echo", vc_command=None).supports("ar")
    assert HybridSingingBackend(svs_command="echo", vc_command="echo").supports("ar")
    assert not HybridSingingBackend(svs_command="echo", vc_command="echo").supports("en")


def test_hybrid_runs_two_stages(tmp_path: Path):
    reference = tmp_path / "reference.wav"
    reference.write_bytes(b"reference")
    output = tmp_path / "generated.wav"

    # Commands are deliberately platform-neutral Python snippets. They create
    # the expected files so the test verifies orchestration without a model.
    import sys
    svs_output = tmp_path / "generated.svs.wav"
    svs_cmd = f'"{sys.executable}" -c "open(r\'{svs_output}\',\'wb\').write(b\'svs\')"'
    vc_cmd = f'"{sys.executable}" -c "open(r\'{output}\',\'wb\').write(open(r\'{svs_output}\',\'rb\').read()+b\'-vc\')"'

    backend = HybridSingingBackend(svs_cmd, vc_cmd)
    result = backend.synthesize(
        SynthesisRequest(
            reference_audio=reference,
            melody_audio=reference,
            reference_lyrics="يا غالية",
            target_lyrics="يا عروسة",
            output_audio=output,
            language="ar",
        )
    )

    assert result.backend == "hybrid_svs_voice_conversion"
    assert output.read_bytes() == b"svs-vc"
