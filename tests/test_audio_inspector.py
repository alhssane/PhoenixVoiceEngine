from pathlib import Path

import numpy as np
import soundfile as sf
import pytest

from src.analyzer.audio_inspector import AudioInspector


def test_inspect_mono_wav(tmp_path: Path):
    path = tmp_path / "voice.wav"
    sf.write(path, np.zeros(44100, dtype=np.float32), 44100)

    report = AudioInspector().inspect(str(path))

    assert report["channels"] == 1
    assert report["sample_rate"] == 44100
    assert report["duration"] == 1.0
    assert report["ready_for_training"] is True


def test_inspect_rejects_unsupported_format(tmp_path: Path):
    path = tmp_path / "voice.txt"
    path.write_text("not audio", encoding="utf-8")

    with pytest.raises(ValueError, match="Unsupported format"):
        AudioInspector().inspect(str(path))


def test_inspect_rejects_missing_file(tmp_path: Path):
    with pytest.raises(FileNotFoundError, match="Audio file not found"):
        AudioInspector().inspect(str(tmp_path / "missing.wav"))
