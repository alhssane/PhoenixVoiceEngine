from pathlib import Path

import pytest

from src.synthesis.production_backend import ProductionSingingBackend
from src.synthesis.synthesis_backend import SynthesisRequest


def test_production_backend_requires_real_model(tmp_path, monkeypatch):
    monkeypatch.delenv("PHOENIX_PRODUCTION_SYNTH_COMMAND", raising=False)
    backend = ProductionSingingBackend()
    assert not backend.supports("ar")
    request = SynthesisRequest(
        reference_audio=tmp_path / "ref.wav",
        melody_audio=tmp_path / "melody.wav",
        reference_lyrics="يا غالية",
        target_lyrics="يا حلوة",
        output_audio=tmp_path / "out.wav",
    )
    with pytest.raises(RuntimeError, match="real singing model"):
        backend.synthesize(request)
