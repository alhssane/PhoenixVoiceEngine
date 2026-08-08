"""
Phoenix Voice Studio
Auto-Fix Engine Test
"""

from pathlib import Path

import soundfile as sf

from src.audio.auto_fix_engine import AutoFixEngine


SOURCE = Path(
    r"F:\من بروتوز\مجلد جديد (2)\يامسهره مقطع.wav"
)

OUTPUT = Path(
    "workspace"
) / "test_audio" / "يامسهره مقطع_autofix.wav"


def test_auto_fix():

    assert SOURCE.exists(), (
        f"Source audio not found: {SOURCE}"
    )

    engine = AutoFixEngine()

    report = engine.process(
        input_path=str(SOURCE),
        output_path=str(OUTPUT),
        convert_stereo=True,
        normalize=False,
    )

    assert OUTPUT.exists()

    audio_data, sample_rate = sf.read(
        str(OUTPUT),
        always_2d=False,
    )

    assert audio_data.ndim == 1

    assert sample_rate == 44100

    assert report.original_channels == 2

    assert report.final_channels == 1

    assert report.mono_converted is True

    assert report.normalized is False


if __name__ == "__main__":

    test_auto_fix()

    print()
    print("=" * 60)
    print("Phoenix Auto-Fix Engine")
    print("=" * 60)
    print("Original : Stereo")
    print("Result   : Mono")
    print("Status   : PASS")
    print("=" * 60)