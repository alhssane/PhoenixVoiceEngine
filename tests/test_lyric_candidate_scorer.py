"""Tests for LyricCandidateScorer V1.0."""

from src.analyzer.lyric_candidate_scorer import LyricCandidateScorer


def make_lyrics():
    return {
        "segments": [
            {"words": [
                {"text": "ألطف", "start_time": 0.0, "end_time": 0.4, "confidence": 95.0},
                {"text": "من", "start_time": 0.4, "end_time": 0.7, "confidence": 99.0},
                {"text": "النسمة", "start_time": 0.7, "end_time": 1.2, "confidence": 98.0},
                {"text": "يا", "start_time": 1.2, "end_time": 1.4, "confidence": 95.0},
                {"text": "بسمة", "start_time": 1.4, "end_time": 1.8, "confidence": 98.0},
                {"text": "ألطف", "start_time": 2.0, "end_time": 2.4, "confidence": 95.0},
                {"text": "من", "start_time": 2.4, "end_time": 2.7, "confidence": 99.0},
                {"text": "النسمة", "start_time": 2.7, "end_time": 3.2, "confidence": 98.0},
            ]}
        ]
    }


def make_candidates():
    return {
        "reports": [
            {
                "word_index": 3,
                "original_text": "السماء",
                "original_confidence": 65.0,
                "start_time": 0.7,
                "end_time": 1.2,
                "candidates": [
                    {
                        "text": "النسمة",
                        "confidence": 93.0,
                        "source": "faster-whisper-redecode",
                        "pass_name": "beam_5",
                        "start_time": 0.7,
                        "end_time": 1.2,
                    },
                    {
                        "text": "السماء",
                        "confidence": 65.0,
                        "source": "original-asr",
                        "pass_name": "original",
                        "start_time": 0.7,
                        "end_time": 1.2,
                    },
                ],
            }
        ]
    }


def test_build():
    result = LyricCandidateScorer().score_report(
        make_candidates(), make_lyrics()
    )
    assert len(result["reports"]) == 1
    print("TEST 1: Build - PASS")


def test_original_preserved():
    result = LyricCandidateScorer().score_report(
        make_candidates(), make_lyrics()
    )
    candidates = result["reports"][0]["candidates"]
    assert any(c["text"] == "السماء" for c in candidates)
    print("TEST 2: Original Preservation - PASS")


def test_repetition_evidence():
    result = LyricCandidateScorer().score_report(
        make_candidates(), make_lyrics()
    )
    candidates = result["reports"][0]["candidates"]
    item = next(c for c in candidates if c["text"] == "النسمة")
    assert item["evidence"]["repetition_support"] > 0
    print("TEST 3: Repetition Evidence - PASS")


def test_confidence_gain():
    result = LyricCandidateScorer().score_report(
        make_candidates(), make_lyrics()
    )
    candidates = result["reports"][0]["candidates"]
    item = next(c for c in candidates if c["text"] == "النسمة")
    assert item["evidence"]["confidence_gain"] == 28.0
    print("TEST 4: Confidence Gain - PASS")


def test_no_auto_correction():
    result = LyricCandidateScorer().score_report(
        make_candidates(), make_lyrics()
    )
    assert result["policy"] == "evidence_only_no_auto_correction"
    assert "selected_candidate" not in result["reports"][0]
    print("TEST 5: No Auto Correction - PASS")


if __name__ == "__main__":
    test_build()
    test_original_preserved()
    test_repetition_evidence()
    test_confidence_gain()
    test_no_auto_correction()
    print("STATUS: PASS")