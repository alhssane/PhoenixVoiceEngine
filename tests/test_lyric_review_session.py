"""
Tests for PhoenixVoiceEngine
Lyric Human Review Session V1.0
"""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

from src.analyzer.lyric_review_session import (
    LyricReviewSession,
)


def build_queue():
    return {
        "engine": "LyricReviewQueue",
        "version": "1.0.1",
        "queue_count": 3,
        "queue": [
            {
                "queue_position": 1,
                "word_index": 1,
                "original_text": "مهابه",
                "candidate_text": "في",
                "candidate_texts": [
                    "في",
                    "مهابه",
                ],
                "original_confidence": 71.52,
                "candidate_confidence": 99.85,
                "start_time": 10.0,
                "end_time": 11.0,
                "priority": "MEDIUM",
                "decision": "REVIEW_CANDIDATE",
                "margin_vs_original": 14.34,
                "independent_support_count": 1,
            },
            {
                "queue_position": 2,
                "word_index": 2,
                "original_text": "تحملها",
                "candidate_text": "كافك",
                "candidate_texts": [
                    "كافك",
                    "تحملها",
                ],
                "original_confidence": 74.41,
                "candidate_confidence": 96.18,
                "start_time": 20.0,
                "end_time": 21.0,
                "priority": "MEDIUM",
                "decision": "REVIEW_CANDIDATE",
                "margin_vs_original": 13.78,
                "independent_support_count": 1,
            },
            {
                "queue_position": 3,
                "word_index": 3,
                "original_text": "الإله",
                "candidate_text": "في",
                "candidate_texts": [
                    "في",
                    "الإله",
                ],
                "original_confidence": 69.69,
                "candidate_confidence": 100.0,
                "start_time": 30.0,
                "end_time": 31.0,
                "priority": "MEDIUM",
                "decision": "REVIEW_CANDIDATE",
                "margin_vs_original": 13.50,
                "independent_support_count": 1,
            },
        ],
    }


def test_build():
    session = LyricReviewSession(
        build_queue()
    )

    assert session.VERSION == "1.0.0"
    assert session.queue_count == 3
    assert session.current_position == 1
    assert session.reviewed_count == 0
    assert session.pending_count == 3
    assert session.completed is False

    print(
        "TEST 1: Build - PASS"
    )


def test_navigation():
    session = LyricReviewSession(
        build_queue()
    )

    assert (
        session.current_item[
            "original_text"
        ]
        == "مهابه"
    )

    session.next()

    assert (
        session.current_item[
            "original_text"
        ]
        == "تحملها"
    )

    session.next()

    assert (
        session.current_item[
            "original_text"
        ]
        == "الإله"
    )

    # Cannot move beyond final item.
    session.next()

    assert (
        session.current_item[
            "original_text"
        ]
        == "الإله"
    )

    session.previous()

    assert (
        session.current_item[
            "original_text"
        ]
        == "تحملها"
    )

    session.goto(1)

    assert (
        session.current_item[
            "original_text"
        ]
        == "مهابه"
    )

    print(
        "TEST 2: Navigation - PASS"
    )


def test_keep_original():
    session = LyricReviewSession(
        build_queue()
    )

    result = session.keep_original(
        note="Human verified original."
    )

    assert (
        result["decision"]
        == "KEEP_ORIGINAL"
    )

    assert (
        result["original_text"]
        == "مهابه"
    )

    assert (
        result["final_text"]
        == "مهابه"
    )

    assert (
        session.reviewed_count == 1
    )

    print(
        "TEST 3: Keep Original - PASS"
    )


def test_accept_candidate():
    session = LyricReviewSession(
        build_queue()
    )

    result = session.accept_candidate()

    assert (
        result["decision"]
        == "ACCEPT_CANDIDATE"
    )

    assert (
        result["final_text"]
        == "في"
    )

    assert (
        result["original_text"]
        == "مهابه"
    )

    print(
        "TEST 4: Accept Candidate - PASS"
    )


def test_custom_correction():
    session = LyricReviewSession(
        build_queue()
    )

    result = session.custom_correction(
        "مهابة",
        note="Human correction."
    )

    assert (
        result["decision"]
        == "CUSTOM_CORRECTION"
    )

    assert (
        result["final_text"]
        == "مهابة"
    )

    print(
        "TEST 5: Custom Correction - PASS"
    )


def test_skip():
    session = LyricReviewSession(
        build_queue()
    )

    result = session.skip(
        note="Need better audio evidence."
    )

    assert (
        result["decision"]
        == "SKIP"
    )

    # Skip never changes the lyric.
    assert (
        result["final_text"]
        == "مهابه"
    )

    print(
        "TEST 6: Skip Protection - PASS"
    )


def test_original_protection():
    session = LyricReviewSession(
        build_queue()
    )

    result = session.keep_original()

    assert (
        result["final_text"]
        == result["original_text"]
    )

    assert (
        result["original_text"]
        == "مهابه"
    )

    print(
        "TEST 7: Original Protection - PASS"
    )


def test_candidate_validation():
    session = LyricReviewSession(
        build_queue()
    )

    try:
        session.accept_candidate(
            "كلمة غير موجودة"
        )
    except ValueError:
        pass
    else:
        raise AssertionError(
            "Invalid candidate was accepted."
        )

    print(
        "TEST 8: Candidate Validation - PASS"
    )


def test_custom_correction_validation():
    session = LyricReviewSession(
        build_queue()
    )

    try:
        session.custom_correction("")
    except ValueError:
        pass
    else:
        raise AssertionError(
            "Empty custom correction was accepted."
        )

    print(
        "TEST 9: Custom Correction Validation - PASS"
    )


def test_statistics():
    session = LyricReviewSession(
        build_queue()
    )

    session.keep_original()

    session.next()

    session.accept_candidate()

    session.next()

    session.skip()

    stats = session.statistics()

    assert (
        stats["queue_count"] == 3
    )

    assert (
        stats["reviewed_count"] == 3
    )

    assert (
        stats["pending_count"] == 0
    )

    assert (
        stats["completed"] is True
    )

    assert (
        stats["decision_counts"][
            "KEEP_ORIGINAL"
        ]
        == 1
    )

    assert (
        stats["decision_counts"][
            "ACCEPT_CANDIDATE"
        ]
        == 1
    )

    assert (
        stats["decision_counts"][
            "SKIP"
        ]
        == 1
    )

    print(
        "TEST 10: Statistics - PASS"
    )


def test_session_serialization():
    session = LyricReviewSession(
        build_queue()
    )

    session.keep_original()

    data = session.to_dict()

    assert (
        data["engine"]
        == "LyricReviewSession"
    )

    assert (
        data["version"]
        == "1.0.0"
    )

    assert (
        data["no_auto_correction"]
        is True
    )

    assert (
        len(data["decisions"])
        == 1
    )

    print(
        "TEST 11: Session Serialization - PASS"
    )


def test_save_session():
    session = LyricReviewSession(
        build_queue()
    )

    session.keep_original()

    with tempfile.TemporaryDirectory() as tmp:
        output = (
            Path(tmp)
            / "review_session.json"
        )

        result = session.save(
            str(output)
        )

        assert output.is_file()

        loaded = json.loads(
            output.read_text(
                encoding="utf-8"
            )
        )

        assert (
            loaded["version"]
            == "1.0.0"
        )

        assert (
            loaded["reviewed_count"]
            == 1
        )

        assert (
            result["reviewed_count"]
            == 1
        )

    print(
        "TEST 12: Save Session - PASS"
    )


def test_final_lyrics_requires_completion():
    session = LyricReviewSession(
        build_queue()
    )

    try:
        session.build_final_lyrics()
    except RuntimeError:
        pass
    else:
        raise AssertionError(
            "Final lyrics were generated "
            "before review completion."
        )

    print(
        "TEST 13: Finalization Protection - PASS"
    )


def test_final_lyrics():
    session = LyricReviewSession(
        build_queue()
    )

    # Word 1 -> keep original
    session.keep_original()

    # Word 2 -> accept candidate
    session.next()
    session.accept_candidate()

    # Word 3 -> custom correction
    session.next()
    session.custom_correction(
        "الإله"
    )

    assert session.completed is True

    result = session.build_final_lyrics()

    assert (
        result["word_count"]
        == 3
    )

    assert (
        result["words"][0][
            "final_text"
        ]
        == "مهابه"
    )

    assert (
        result["words"][1][
            "final_text"
        ]
        == "كافك"
    )

    assert (
        result["words"][2][
            "final_text"
        ]
        == "الإله"
    )

    assert (
        result["no_auto_correction"]
        is True
    )

    print(
        "TEST 14: Final Lyrics - PASS"
    )


def test_final_lyrics_preserve_order():
    session = LyricReviewSession(
        build_queue()
    )

    session.goto(3)
    session.custom_correction(
        "الإله"
    )

    session.goto(1)
    session.keep_original()

    session.goto(2)
    session.accept_candidate()

    result = session.build_final_lyrics()

    indices = [
        word["word_index"]
        for word in result["words"]
    ]

    assert indices == [
        1,
        2,
        3,
    ]

    print(
        "TEST 15: Final Order Preservation - PASS"
    )


def test_no_auto_correction():
    session = LyricReviewSession(
        build_queue()
    )

    # Merely loading the queue must not
    # create any decisions.
    assert (
        session.reviewed_count == 0
    )

    assert (
        session.pending_count == 3
    )

    # Moving through the queue must not
    # create decisions.
    session.next()
    session.next()
    session.previous()

    assert (
        session.reviewed_count == 0
    )

    print(
        "TEST 16: No Auto Correction - PASS"
    )


if __name__ == "__main__":
    test_build()
    test_navigation()
    test_keep_original()
    test_accept_candidate()
    test_custom_correction()
    test_skip()
    test_original_protection()
    test_candidate_validation()
    test_custom_correction_validation()
    test_statistics()
    test_session_serialization()
    test_save_session()
    test_final_lyrics_requires_completion()
    test_final_lyrics()
    test_final_lyrics_preserve_order()
    test_no_auto_correction()

    print(
        "STATUS: PASS"
    )