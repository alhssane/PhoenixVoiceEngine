"""
PhoenixVoiceEngine - Lyric Context Analyzer V1.0 tests
"""

from src.analyzer.lyric_context_analyzer import LyricContextAnalyzer


def make_lyrics():
    # Repeated structure:
    # يا ريمه طلي الجميل
    # يا ريمه طلي الجميل
    return {
        "segments": [
            {
                "words": [
                    {"index": 1, "text": "يا", "start_time": 0.0, "end_time": 0.5},
                    {"index": 2, "text": "ريمة", "start_time": 0.5, "end_time": 1.0},
                    {"index": 3, "text": "طلي", "start_time": 1.0, "end_time": 1.5},
                    {"index": 4, "text": "الجمال", "start_time": 1.5, "end_time": 2.0},
                    {"index": 5, "text": "يا", "start_time": 2.0, "end_time": 2.5},
                    {"index": 6, "text": "ريمة", "start_time": 2.5, "end_time": 3.0},
                    {"index": 7, "text": "طلي", "start_time": 3.0, "end_time": 3.5},
                    {"index": 8, "text": "الجمال", "start_time": 3.5, "end_time": 4.0},
                ]
            }
        ]
    }


def make_candidates():
    return {
        "reports": [
            {
                "word_index": 3,
                "original_text": "طلي",
                "original_confidence": 70.0,
                "start_time": 1.0,
                "end_time": 1.5,
                "candidates": [
                    {
                        "text": "طلي",
                        "confidence": 70.0,
                        "source": "original-asr",
                        "pass_name": "original",
                        "start_time": 1.0,
                        "end_time": 1.5,
                    },
                    {
                        "text": "طلي",
                        "confidence": 80.0,
                        "source": "redecode",
                        "pass_name": "beam_10",
                        "start_time": 1.0,
                        "end_time": 1.5,
                    },
                    {
                        "text": "ريما",
                        "confidence": 90.0,
                        "source": "redecode",
                        "pass_name": "beam_10",
                        "start_time": 1.0,
                        "end_time": 1.5,
                    },
                ],
            }
        ]
    }


def test_build():
    engine = LyricContextAnalyzer()
    assert engine.VERSION == "1.0.0"
    print("TEST 1: Build - PASS")


def test_position_alignment():
    engine = LyricContextAnalyzer()
    result = engine.analyze(make_lyrics(), make_candidates())
    candidates = result["reports"][0]["context_candidates"]

    aligned = [x for x in candidates if x["text"] == "طلي"]
    assert aligned
    assert aligned[0]["context"]["position_score"] >= 99.0
    print("TEST 2: Position Alignment - PASS")


def test_repeated_context_support():
    engine = LyricContextAnalyzer()
    result = engine.analyze(make_lyrics(), make_candidates())
    candidates = result["reports"][0]["context_candidates"]

    original = next(x for x in candidates if x["text"] == "طلي")
    assert original["context"]["repeated_context_score"] == 100.0
    assert original["context"]["previous_neighbor_score"] == 100.0
    assert original["context"]["next_neighbor_score"] == 100.0
    print("TEST 3: Repeated Context Support - PASS")


def test_unrelated_candidate_not_supported():
    engine = LyricContextAnalyzer()
    result = engine.analyze(make_lyrics(), make_candidates())
    candidates = result["reports"][0]["context_candidates"]

    unrelated = next(x for x in candidates if x["text"] == "ريما")
    assert unrelated["context"]["repeated_context_score"] == 0.0
    assert unrelated["context"]["decision"] in {
        "NO_CONTEXT_SUPPORT",
        "WEAK_CONTEXT",
    }
    print("TEST 4: Unrelated Candidate Rejection - PASS")


def test_no_auto_correction():
    engine = LyricContextAnalyzer()
    result = engine.analyze(make_lyrics(), make_candidates())

    assert "selected_candidate" not in result["reports"][0]
    assert "corrected_text" not in result
    assert result["reports"][0]["original_text"] == "طلي"
    print("TEST 5: No Auto Correction - PASS")


def test_output_structure():
    engine = LyricContextAnalyzer()
    result = engine.analyze(make_lyrics(), make_candidates())

    assert result["engine"] == "LyricContextAnalyzer"
    assert result["version"] == "1.0.0"
    assert result["report_count"] == 1

    evidence = result["reports"][0]["context_candidates"][0]["context"]
    required = {
        "position_score",
        "previous_neighbor_score",
        "next_neighbor_score",
        "repeated_context_score",
        "phrase_support_score",
        "contrast_score",
        "total_score",
        "decision",
        "reasons",
    }
    assert required.issubset(evidence.keys())
    print("TEST 6: Output Structure - PASS")


if __name__ == "__main__":
    test_build()
    test_position_alignment()
    test_repeated_context_support()
    test_unrelated_candidate_not_supported()
    test_no_auto_correction()
    test_output_structure()
    print("STATUS: PASS")