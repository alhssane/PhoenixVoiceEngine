from __future__ import annotations

import json
import tempfile
from pathlib import Path

from src.analyzer.lyric_quality_assurance import (
    LyricQualityAssurance,
)


def make_items():

    return [
        {
            "position": 1,
            "original_text": "كلمة",
            "final_text": "كلمة",
            "decision": "KEEP_ORIGINAL",
            "start_time": 1.0,
            "end_time": 2.0,
        },
        {
            "position": 2,
            "original_text": "ثانية",
            "final_text": "بديل",
            "decision": "ACCEPT_CANDIDATE",
            "start_time": 2.0,
            "end_time": 3.0,
        },
        {
            "position": 3,
            "original_text": "ثالثة",
            "final_text": "تصحيح",
            "decision": "CUSTOM_CORRECTION",
            "start_time": 3.0,
            "end_time": 4.0,
        },
        {
            "position": 4,
            "original_text": "رابعة",
            "final_text": "رابعة",
            "decision": "SKIP",
            "start_time": 4.0,
            "end_time": 5.0,
        },
    ]


def make_data():

    return {
        "version": "1.0.0",
        "source": "LyricReviewSession",
        "item_count": 4,
        "items": make_items(),
    }


def test_build():

    engine = LyricQualityAssurance()

    assert engine.VERSION == "1.0.0"

    print("TEST 1: Build - PASS")


def test_clean_lyrics_pass():

    engine = LyricQualityAssurance()

    result = engine.analyze(
        make_data()
    )

    assert result["status"] == "PASS"
    assert result["fail_count"] == 0

    print("TEST 2: Clean Lyrics - PASS")


def test_empty_text_detection():

    engine = LyricQualityAssurance()

    data = make_data()

    data["items"][1][
        "final_text"
    ] = ""

    result = engine.analyze(
        data
    )

    assert (
        result["warning_count"] >= 1
    )

    assert any(
        issue["type"]
        == "EMPTY_FINAL_TEXT"
        for issue in result["issues"]
    )

    print(
        "TEST 3: Empty Text Detection - PASS"
    )


def test_invalid_duration():

    engine = LyricQualityAssurance()

    data = make_data()

    data["items"][1][
        "end_time"
    ] = 1.5

    result = engine.analyze(
        data
    )

    assert (
        result["status"] == "FAIL"
    )

    assert any(
        issue["type"]
        == "INVALID_DURATION"
        for issue in result["issues"]
    )

    print(
        "TEST 4: Invalid Duration - PASS"
    )


def test_overlap_detection():

    engine = LyricQualityAssurance()

    data = make_data()

    data["items"][1][
        "start_time"
    ] = 1.5

    result = engine.analyze(
        data
    )

    assert any(
        issue["type"]
        == "TIMING_OVERLAP"
        for issue in result["issues"]
    )

    print(
        "TEST 5: Timing Overlap - PASS"
    )


def test_order_validation():

    engine = LyricQualityAssurance()

    data = make_data()

    data["items"][2][
        "position"
    ] = 8

    result = engine.analyze(
        data
    )

    assert (
        result["status"] == "FAIL"
    )

    assert any(
        issue["type"]
        == "ORDER_MISMATCH"
        for issue in result["issues"]
    )

    print(
        "TEST 6: Order Validation - PASS"
    )


def test_duplicate_detection():

    engine = LyricQualityAssurance(
        duplicate_threshold=2
    )

    data = make_data()

    data["items"][1][
        "final_text"
    ] = "كلمة"

    result = engine.analyze(
        data
    )

    assert any(
        issue["type"]
        == "REPEATED_LYRIC_SEQUENCE"
        for issue in result["issues"]
    )

    print(
        "TEST 7: Duplicate Sequence Detection - PASS"
    )


def test_original_consistency():

    engine = LyricQualityAssurance()

    data = make_data()

    data["items"][0][
        "final_text"
    ] = "تغيير"

    result = engine.analyze(
        data
    )

    assert (
        result["status"] == "FAIL"
    )

    assert any(
        issue["type"]
        == "ORIGINAL_MISMATCH"
        for issue in result["issues"]
    )

    print(
        "TEST 8: Original Consistency - PASS"
    )


def test_invalid_decision():

    engine = LyricQualityAssurance()

    data = make_data()

    data["items"][0][
        "decision"
    ] = "AUTO_CORRECT"

    result = engine.analyze(
        data
    )

    assert (
        result["status"] == "FAIL"
    )

    assert any(
        issue["type"]
        == "INVALID_DECISION"
        for issue in result["issues"]
    )

    print(
        "TEST 9: Invalid Decision Protection - PASS"
    )


def test_negative_time():

    engine = LyricQualityAssurance()

    data = make_data()

    data["items"][0][
        "start_time"
    ] = -1.0

    result = engine.analyze(
        data
    )

    assert (
        result["status"] == "FAIL"
    )

    assert any(
        issue["type"]
        == "NEGATIVE_START_TIME"
        for issue in result["issues"]
    )

    print(
        "TEST 10: Negative Timing Protection - PASS"
    )


def test_no_auto_correction():

    engine = LyricQualityAssurance()

    data = make_data()

    original = data["items"][0][
        "final_text"
    ]

    result = engine.analyze(
        data
    )

    assert (
        data["items"][0]["final_text"]
        == original
    )

    assert result["issues"] is not None

    print(
        "TEST 11: No Auto Correction - PASS"
    )


def test_output_structure():

    engine = LyricQualityAssurance()

    result = engine.analyze(
        make_data()
    )

    assert "version" in result
    assert "status" in result
    assert "item_count" in result
    assert "issue_count" in result
    assert "fail_count" in result
    assert "warning_count" in result
    assert "checks" in result
    assert "issues" in result

    assert result["checks"][
        "timing"
    ]

    assert result["checks"][
        "consistency"
    ]

    print(
        "TEST 12: Output Structure - PASS"
    )


def test_file_analysis():

    engine = LyricQualityAssurance()

    with tempfile.TemporaryDirectory() as tmp:

        root = Path(tmp)

        input_path = (
            root / "final.json"
        )

        output_path = (
            root / "qa.json"
        )

        input_path.write_text(
            json.dumps(
                make_data(),
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )

        result = engine.analyze_file(
            input_path,
            output_path,
        )

        assert output_path.exists()
        assert result["status"] == "PASS"

        saved = json.loads(
            output_path.read_text(
                encoding="utf-8"
            )
        )

        assert saved["version"] == "1.0.0"

    print(
        "TEST 13: File Analysis - PASS"
    )


if __name__ == "__main__":

    print("=" * 60)
    print("PhoenixVoiceEngine")
    print("Lyric Quality Assurance V1.0")
    print("=" * 60)

    test_build()
    test_clean_lyrics_pass()
    test_empty_text_detection()
    test_invalid_duration()
    test_overlap_detection()
    test_order_validation()
    test_duplicate_detection()
    test_original_consistency()
    test_invalid_decision()
    test_negative_time()
    test_no_auto_correction()
    test_output_structure()
    test_file_analysis()

    print("=" * 60)
    print("STATUS: PASS")
    print("=" * 60)