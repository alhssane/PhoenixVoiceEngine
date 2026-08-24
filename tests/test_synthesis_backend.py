from pathlib import Path

import pytest

from src.synthesis.command_backend import CommandSynthesisBackend
from src.synthesis.synthesis_backend import SynthesisRequest


def test_command_backend_requires_configuration(monkeypatch):
    monkeypatch.delenv("PHOENIX_SYNTH_COMMAND", raising=False)
    backend = CommandSynthesisBackend()
    assert not backend.supports("ar")
    with pytest.raises(RuntimeError, match="not configured"):
        backend.synthesize(
            SynthesisRequest(
                reference_audio=Path("ref.wav"),
                melody_audio=Path("melody.wav"),
                reference_lyrics="الأصل",
                target_lyrics="الجديد",
                output_audio=Path("out.wav"),
            )
        )


def test_synthesis_request_defaults_to_arabic():
    request = SynthesisRequest(
        reference_audio=Path("ref.wav"),
        melody_audio=Path("melody.wav"),
        reference_lyrics="الأصل",
        target_lyrics="الجديد",
        output_audio=Path("out.wav"),
    )
    assert request.language == "ar"
    assert request.preserve_style is True
    assert request.preserve_melody is True
