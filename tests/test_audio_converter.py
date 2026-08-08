"""
Phoenix Voice Studio
Audio Converter Tests
"""

from pathlib import Path

import soundfile as sf

from src.audio.audio_converter import AudioConverter


TEST_AUDIO = Path(r"F:\من بروتوز\مجلد جديد (2)\يامسهره مقطع.wav")

TEST_OUTPUT = Path("workspace") / "test_audio" / "يامسهره مقطع_mono.wav"


def test_convert_stereo_to_mono():

    assert TEST_AUDIO.exists(), (
        f"Test audio file not found: {TEST_AUDIO}"
    )

    output_path = AudioConverter.convert_file_to_mono(
        str(TEST_AUDIO),
        str(TEST_OUTPUT),
    )

    assert Path(output_path).exists()

    audio_data, sample_rate = sf.read(
        output_path,
        always_2d=False,
    )

    assert audio_data.ndim == 1

    assert sample_rate == 44100


if __name__ == "__main__":
    test_convert_stereo_to_mono()

    print()
    print("=" * 50)
    print("AudioConverter Test")
    print("=" * 50)
    print("PASS: Stereo → Mono")
    print("=" * 50)