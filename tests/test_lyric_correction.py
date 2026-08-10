"""Tests for PhoenixVoiceEngine LyricCorrectionEngine."""

from src.analyzer.lyric_correction import LyricCorrectionEngine


def make_report():
    return {
        "duration": 4.0,
        "language": "ar",
        "segments": [
            {"words": [
                {"text": "بسمة", "start_time": 0.0, "end_time": 0.5, "confidence": 99.0},
                {"text": "الغلاء", "start_time": 0.5, "end_time": 1.0, "confidence": 99.0},
            ]},
            {"words": [
                {"text": "بسمة", "start_time": 1.0, "end_time": 1.5, "confidence": 99.0},
                {"text": "الغلا", "start_time": 1.5, "end_time": 2.0, "confidence": 70.0},
            ]},
        ],
    }


def test_build():
    result = LyricCorrectionEngine().correct_report(make_report())
    assert result["correction"]["total_word_count"] == 4
    print("TEST 1: Build - PASS")


def test_high_confidence_preserved():
    result = LyricCorrectionEngine().correct_report(make_report())
    assert result["segments"][0]["words"][0]["text"] == "بسمة"
    print("TEST 2: High Confidence Preservation - PASS")


def test_timing_preserved():
    result = LyricCorrectionEngine().correct_report(make_report())
    word = result["segments"][1]["words"][1]
    assert word["start_time"] == 1.5
    assert word["end_time"] == 2.0
    print("TEST 3: Timing Preservation - PASS")


def test_output():
    result = LyricCorrectionEngine().correct_report(make_report())
    assert isinstance(result["corrected_text"], str)
    assert "correction" in result
    print("TEST 4: Output Structure - PASS")


if __name__ == "__main__":
    for fn in (
        test_build,
        test_high_confidence_preserved,
        test_timing_preserved,
        test_output,
    ):
        fn()
    print("STATUS: PASS")