"""
Phoenix Voice Studio
Audio Quality Engine Test
"""

from pathlib import Path

from src.analyzer.audio_quality_engine import AudioQualityEngine


SOURCE = Path(
    r"F:\من بروتوز\مجلد جديد (2)\يامسهره مقطع.wav"
)


def test_audio_quality_engine():

    assert SOURCE.exists(), (
        f"Audio file not found: {SOURCE}"
    )

    engine = AudioQualityEngine()

    report = engine.analyze(
        str(SOURCE)
    )

    assert report.duration > 0

    assert report.sample_rate == 44100

    assert report.channels == 2

    assert 0 <= report.technical_score <= 100

    assert 0 <= report.signal_score <= 100

    assert 0 <= report.training_suitability <= 100

    assert report.status in {
        "READY",
        "READY_WITH_PROCESSING",
        "NEEDS_PROCESSING",
        "LOW_QUALITY",
        "NOT_SUITABLE",
    }


if __name__ == "__main__":

    report = AudioQualityEngine().analyze(
        str(SOURCE)
    )

    print()
    print("=" * 60)
    print("Phoenix Audio Quality Engine")
    print("=" * 60)

    print(
        f"File               : {report.file_name}"
    )

    print(
        f"Duration           : {report.duration} sec"
    )

    print(
        f"Sample Rate        : {report.sample_rate} Hz"
    )

    print(
        f"Channels           : {report.channels}"
    )

    print(
        f"Peak               : {report.peak_dbfs} dBFS"
    )

    print(
        f"RMS                : {report.rms_dbfs} dBFS"
    )

    print(
        f"Clipping Ratio     : {report.clipping_ratio}"
    )

    print(
        f"Silence Ratio      : {report.silence_ratio}"
    )

    print(
        f"Dynamic Range      : {report.dynamic_range_db} dB"
    )

    print(
        f"Technical Score    : {report.technical_score}/100"
    )

    print(
        f"Signal Score       : {report.signal_score}/100"
    )

    print(
        f"Training Suitability: "
        f"{report.training_suitability}/100"
    )

    print(
        f"Status             : {report.status}"
    )

    print()
    print("Recommendations")
    print("-" * 60)

    for recommendation in report.recommendations:
        print(f"- {recommendation}")

    print()
    print("STATUS: PASS")
    print("=" * 60)