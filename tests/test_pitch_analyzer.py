from __future__ import annotations

import json
import math
import tempfile
import wave
from pathlib import Path

import numpy as np

from src.pitch.pitch_analyzer import PitchAnalyzer


def create_sine_wav(
    path: Path,
    frequency: float = 220.0,
    duration: float = 1.0,
    sample_rate: int = 16000,
) -> None:

    sample_count = int(
        duration * sample_rate
    )

    t = np.arange(
        sample_count,
        dtype=np.float32,
    ) / sample_rate

    signal = (
        0.5
        * np.sin(
            2.0
            * math.pi
            * frequency
            * t
        )
    )

    signal = np.clip(
        signal,
        -1.0,
        1.0,
    )

    pcm = (
        signal
        * 32767
    ).astype(
        np.int16
    )

    with wave.open(
        str(path),
        "wb",
    ) as wav:

        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(
            sample_rate
        )
        wav.writeframes(
            pcm.tobytes()
        )


def create_silence_wav(
    path: Path,
    duration: float = 1.0,
    sample_rate: int = 16000,
) -> None:

    sample_count = int(
        duration * sample_rate
    )

    pcm = np.zeros(
        sample_count,
        dtype=np.int16,
    )

    with wave.open(
        str(path),
        "wb",
    ) as wav:

        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(
            sample_rate
        )
        wav.writeframes(
            pcm.tobytes()
        )


def test_build():

    engine = PitchAnalyzer()

    assert engine.VERSION == "1.0.0"
    assert engine.sample_rate == 16000
    assert engine.hop_length == 160
    assert engine.frame_length == 2048

    print(
        "TEST 1: Build - PASS"
    )


def test_audio_loading():

    with tempfile.TemporaryDirectory() as tmp:

        root = Path(tmp)

        audio = (
            root
            / "test.wav"
        )

        create_sine_wav(
            audio
        )

        engine = PitchAnalyzer()

        y, sr = engine.load_audio(
            audio
        )

        assert isinstance(
            y,
            np.ndarray,
        )

        assert len(y) > 0
        assert sr == 16000

    print(
        "TEST 2: Audio Loading - PASS"
    )


def test_pitch_detection():

    with tempfile.TemporaryDirectory() as tmp:

        root = Path(tmp)

        audio = (
            root
            / "sine_220.wav"
        )

        create_sine_wav(
            audio,
            frequency=220.0,
        )

        engine = PitchAnalyzer()

        y, sr = engine.load_audio(
            audio
        )

        result = engine.analyze(
            y,
            sr,
            source_path=audio,
        )

        statistics = result[
            "pitch"
        ][
            "statistics"
        ]

        assert (
            statistics[
                "f0_mean_hz"
            ]
            is not None
        )

        assert abs(
            statistics[
                "f0_mean_hz"
            ]
            - 220.0
        ) < 10.0

    print(
        "TEST 3: Pitch Detection - PASS"
    )


def test_pitch_frames():

    with tempfile.TemporaryDirectory() as tmp:

        root = Path(tmp)

        audio = (
            root
            / "test.wav"
        )

        create_sine_wav(
            audio
        )

        engine = PitchAnalyzer()

        y, sr = engine.load_audio(
            audio
        )

        result = engine.analyze(
            y,
            sr,
        )

        frames = result[
            "pitch"
        ][
            "frames"
        ]

        assert len(
            frames
        ) > 0

        first = frames[0]

        assert (
            "frame_index"
            in first
        )

        assert (
            "time"
            in first
        )

        assert (
            "f0_hz"
            in first
        )

        assert (
            "voiced"
            in first
        )

        assert (
            "voiced_probability"
            in first
        )

    print(
        "TEST 4: Pitch Frames - PASS"
    )


def test_pitch_statistics():

    with tempfile.TemporaryDirectory() as tmp:

        root = Path(tmp)

        audio = (
            root
            / "test.wav"
        )

        create_sine_wav(
            audio,
            frequency=220.0,
        )

        engine = PitchAnalyzer()

        y, sr = engine.load_audio(
            audio
        )

        result = engine.analyze(
            y,
            sr,
        )

        stats = result[
            "pitch"
        ][
            "statistics"
        ]

        assert (
            stats[
                "voiced_frame_count"
            ]
            > 0
        )

        assert (
            stats[
                "voiced_ratio"
            ]
            > 0.5
        )

        assert (
            stats[
                "f0_min_hz"
            ]
            is not None
        )

        assert (
            stats[
                "f0_max_hz"
            ]
            is not None
        )

        assert (
            stats[
                "f0_mean_hz"
            ]
            is not None
        )

    print(
        "TEST 5: Pitch Statistics - PASS"
    )


def test_silence_protection():

    with tempfile.TemporaryDirectory() as tmp:

        root = Path(tmp)

        audio = (
            root
            / "silence.wav"
        )

        create_silence_wav(
            audio
        )

        engine = PitchAnalyzer()

        y, sr = engine.load_audio(
            audio
        )

        result = engine.analyze(
            y,
            sr,
        )

        stats = result[
            "pitch"
        ][
            "statistics"
        ]

        assert (
            stats[
                "voiced_ratio"
            ]
            < 0.5
        )

        assert (
            stats[
                "f0_mean_hz"
            ]
            is None
        )

    print(
        "TEST 6: Silence Protection - PASS"
    )


def test_invalid_audio_protection():

    with tempfile.TemporaryDirectory() as tmp:

        root = Path(tmp)

        missing = (
            root
            / "missing.wav"
        )

        engine = PitchAnalyzer()

        try:

            engine.load_audio(
                missing
            )

            raise AssertionError(
                "Expected FileNotFoundError"
            )

        except FileNotFoundError:
            pass

    print(
        "TEST 7: Invalid Audio Protection - PASS"
    )


def test_output_structure():

    with tempfile.TemporaryDirectory() as tmp:

        root = Path(tmp)

        audio = (
            root
            / "test.wav"
        )

        output = (
            root
            / "pitch.json"
        )

        create_sine_wav(
            audio
        )

        engine = PitchAnalyzer()

        result = engine.analyze_file(
            audio,
            output,
        )

        assert output.exists()

        assert result[
            "version"
        ] == "1.0.0"

        assert (
            "audio"
            in result
        )

        assert (
            "pitch"
            in result
        )

        assert (
            "frames"
            in result[
                "pitch"
            ]
        )

        saved = json.loads(
            output.read_text(
                encoding="utf-8"
            )
        )

        assert (
            saved[
                "pitch"
            ][
                "frame_count"
            ]
            > 0
        )

    print(
        "TEST 8: Output Structure - PASS"
    )


if __name__ == "__main__":

    print(
        "=" * 60
    )

    print(
        "PhoenixVoiceEngine"
    )

    print(
        "Pitch Analyzer V1.0"
    )

    print(
        "=" * 60
    )

    test_build()
    test_audio_loading()
    test_pitch_detection()
    test_pitch_frames()
    test_pitch_statistics()
    test_silence_protection()
    test_invalid_audio_protection()
    test_output_structure()

    print(
        "=" * 60
    )

    print(
        "STATUS: PASS"
    )

    print(
        "=" * 60
    )