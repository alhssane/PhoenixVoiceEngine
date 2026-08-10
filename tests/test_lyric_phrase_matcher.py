"""Tests for PhoenixVoiceEngine LyricPhraseMatcher."""

from src.analyzer.lyric_phrase_matcher import LyricPhraseMatcher


def synthetic_report():
    return {
        "segments": [
            {
                "words": [
                    {"text": "يا", "start_time": 0.0, "end_time": 0.3, "confidence": 95.0},
                    {"text": "بسمة", "start_time": 0.3, "end_time": 0.8, "confidence": 95.0},
                    {"text": "يا", "start_time": 0.8, "end_time": 1.0, "confidence": 95.0},
                    {"text": "كل", "start_time": 1.0, "end_time": 1.3, "confidence": 95.0},
                    {"text": "الهنى", "start_time": 1.3, "end_time": 1.8, "confidence": 95.0},
                    {"text": "يا", "start_time": 3.0, "end_time": 3.3, "confidence": 95.0},
                    {"text": "بسمة", "start_time": 3.3, "end_time": 3.8, "confidence": 95.0},
                    {"text": "يا", "start_time": 3.8, "end_time": 4.0, "confidence": 95.0},
                    {"text": "كل", "start_time": 4.0, "end_time": 4.3, "confidence": 95.0},
                    {"text": "الهنى", "start_time": 4.3, "end_time": 4.8, "confidence": 95.0},
                ]
            }
        ]
    }


def test_build():
    result = LyricPhraseMatcher(min_phrase_words=3, max_phrase_words=5).analyze_report(
        synthetic_report()
    )
    assert result["match_count"] > 0
    print("TEST 1: Repeated Phrase Detection - PASS")


def test_difference_detection():
    report = synthetic_report()
    report["segments"][0]["words"][8]["text"] = "الهناء"
    result = LyricPhraseMatcher(min_phrase_words=3, max_phrase_words=5).analyze_report(report)

    assert any(
        item["differing_positions"]
        for item in result["matches"]
    )
    print("TEST 2: Difference Detection - PASS")


def test_timing():
    result = LyricPhraseMatcher(min_phrase_words=3, max_phrase_words=5).analyze_report(
        synthetic_report()
    )
    match = result["matches"][0]
    assert match["first_start"] < match["first_end"]
    assert match["second_start"] < match["second_end"]
    print("TEST 3: Timing Preservation - PASS")


def test_serializable():
    result = LyricPhraseMatcher(min_phrase_words=3, max_phrase_words=5).analyze_report(
        synthetic_report()
    )
    assert isinstance(result["matches"], list)
    print("TEST 4: Output Structure - PASS")


if __name__ == "__main__":
    for fn in (
        test_build,
        test_difference_detection,
        test_timing,
        test_serializable,
    ):
        fn()

    print("STATUS: PASS")