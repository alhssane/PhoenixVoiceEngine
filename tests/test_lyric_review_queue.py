"""
PhoenixVoiceEngine - Lyric Review Queue V1.0 tests
"""

from __future__ import annotations

from src.analyzer.lyric_review_queue import (
    LyricReviewQueue,
)


def make_candidate(
    text,
    decision,
    margin,
    supports,
    total_score=70.0,
    confidence=80.0,
):
    return {
        "text": text,
        "evidence": {
            "asr_confidence": confidence,
        },
        "fusion": {
            "candidate_score": total_score,
            "candidate_acoustic_score": confidence,
            "confidence_gain": 10.0,
            "context_score": 80.0,
            "repeated_context_score": 80.0,
            "phrase_support_score": 80.0,
            "position_score": 95.0,
            "candidate_total_score": total_score,
            "original_total_score": total_score - margin,
            "margin_vs_original": margin,
            "relative_margin": margin,
            "independent_support_count": supports,
            "decision": decision,
            "reasons": [
                "test evidence"
            ],
        },
    }


def make_report(
    index,
    original,
    confidence,
    candidates,
):
    return {
        "word_index": index,
        "original_text": original,
        "original_confidence": confidence,
        "start_time": 1.0,
        "end_time": 2.0,
        "candidates": candidates,
    }


def make_fusion(reports):
    return {
        "engine": "LyricEvidenceFusion",
        "version": "1.1.1",
        "mode": "comparative_decision_engine",
        "policy": "evidence_only_no_auto_correction",
        "reports": reports,
    }


def test_build():
    engine = LyricReviewQueue()

    assert engine.VERSION == "1.0.1"
    assert engine.min_margin == 0.0
    assert engine.min_supports == 1

    print("TEST 1: Build - PASS")


def test_review_candidate_is_queued():
    fusion = make_fusion(
        [
            make_report(
                1,
                "طلي",
                75.0,
                [
                    make_candidate(
                        "طلي",
                        "KEEP_ORIGINAL",
                        0.0,
                        3,
                    ),
                    make_candidate(
                        "طلعي",
                        "REVIEW_CANDIDATE",
                        12.0,
                        2,
                    ),
                ],
            )
        ]
    )

    engine = LyricReviewQueue()
    result = engine.analyze(fusion)

    assert result["queue_count"] == 1

    item = result["queue"][0]

    assert item["original_text"] == "طلي"
    assert item["candidate_text"] == "طلعي"
    assert item["decision"] == "REVIEW_CANDIDATE"
    assert item["status"] == "PENDING_REVIEW"

    print("TEST 2: Review Candidate Queue - PASS")


def test_original_is_never_queued():
    fusion = make_fusion(
        [
            make_report(
                1,
                "طلي",
                75.0,
                [
                    make_candidate(
                        "طلي",
                        "KEEP_ORIGINAL",
                        0.0,
                        3,
                    ),
                ],
            )
        ]
    )

    result = LyricReviewQueue().analyze(fusion)

    assert result["queue_count"] == 0
    assert result["queue"] == []

    print("TEST 3: Original Protection - PASS")


def test_negative_margin_is_not_queued():
    fusion = make_fusion(
        [
            make_report(
                1,
                "طلي",
                75.0,
                [
                    make_candidate(
                        "وقبل",
                        "KEEP_ORIGINAL",
                        -15.0,
                        2,
                    ),
                ],
            )
        ]
    )

    result = LyricReviewQueue().analyze(fusion)

    assert result["queue_count"] == 0

    print("TEST 4: Negative Margin Protection - PASS")


def test_single_evidence_can_be_reviewed():
    fusion = make_fusion(
        [
            make_report(
                1,
                "تحملها",
                74.0,
                [
                    make_candidate(
                        "كافك",
                        "REVIEW_CANDIDATE",
                        13.0,
                        1,
                    ),
                ],
            )
        ]
    )

    engine = LyricReviewQueue(
        min_supports=1
    )

    result = engine.analyze(fusion)

    assert result["queue_count"] == 1
    assert (
        result["queue"][0]["candidate_text"]
        == "كافك"
    )

    print("TEST 5: Single Evidence Review - PASS")


def test_two_evidence_has_higher_priority():
    fusion = make_fusion(
        [
            make_report(
                1,
                "كلمة",
                75.0,
                [
                    make_candidate(
                        "مرشح1",
                        "REVIEW_CANDIDATE",
                        8.0,
                        1,
                    ),
                ],
            ),
            make_report(
                2,
                "كلمة2",
                75.0,
                [
                    make_candidate(
                        "مرشح2",
                        "REVIEW_CANDIDATE",
                        8.0,
                        2,
                    ),
                ],
            ),
        ]
    )

    result = LyricReviewQueue().analyze(
        fusion
    )

    assert result["queue_count"] == 2

    first = result["queue"][0]
    second = result["queue"][1]

    assert (
        first["independent_support_count"]
        >= second["independent_support_count"]
    )

    print("TEST 6: Evidence Priority - PASS")


def test_recommendation_is_queued():
    fusion = make_fusion(
        [
            make_report(
                1,
                "أغلى",
                77.0,
                [
                    make_candidate(
                        "عطاك",
                        "RECOMMEND_CORRECTION",
                        18.0,
                        3,
                    ),
                ],
            )
        ]
    )

    result = LyricReviewQueue().analyze(
        fusion
    )

    assert result["queue_count"] == 1

    item = result["queue"][0]

    assert (
        item["decision"]
        == "RECOMMEND_CORRECTION"
    )

    print("TEST 7: Recommendation Queue - PASS")


def test_strong_correction_is_queued():
    fusion = make_fusion(
        [
            make_report(
                1,
                "أنت",
                48.0,
                [
                    make_candidate(
                        "انتي",
                        "STRONG_CORRECTION",
                        25.0,
                        3,
                        total_score=90.0,
                    ),
                ],
            )
        ]
    )

    result = LyricReviewQueue().analyze(
        fusion
    )

    assert result["queue_count"] == 1
    assert (
        result["queue"][0]["priority"]
        == "HIGH"
    )

    print("TEST 8: Strong Correction Queue - PASS")


def test_output_structure():
    fusion = make_fusion(
        [
            make_report(
                1,
                "طلي",
                75.0,
                [
                    make_candidate(
                        "طلعي",
                        "REVIEW_CANDIDATE",
                        12.0,
                        2,
                    ),
                ],
            )
        ]
    )

    result = LyricReviewQueue().analyze(
        fusion
    )

    required = {
        "engine",
        "version",
        "source_engine",
        "source_version",
        "mode",
        "policy",
        "source_report_count",
        "queue_count",
        "priority_counts",
        "decision_counts",
        "queue",
    }

    assert required.issubset(
        result.keys()
    )

    item = result["queue"][0]

    required_item = {
        "review_id",
        "queue_position",
        "word_index",
        "original_text",
        "candidate_text",
        "original_confidence",
        "candidate_confidence",
        "start_time",
        "end_time",
        "duration",
        "priority",
        "decision",
        "candidate_total_score",
        "original_total_score",
        "margin_vs_original",
        "relative_margin",
        "independent_support_count",
        "evidence",
        "reasons",
        "status",
    }

    assert required_item.issubset(
        item.keys()
    )

    print("TEST 9: Output Structure - PASS")


def test_no_auto_correction():
    fusion = make_fusion(
        [
            make_report(
                1,
                "طلي",
                75.0,
                [
                    make_candidate(
                        "طلعي",
                        "STRONG_CORRECTION",
                        30.0,
                        4,
                    ),
                ],
            )
        ]
    )

    result = LyricReviewQueue().analyze(
        fusion
    )

    item = result["queue"][0]

    # The original remains untouched.
    assert item["original_text"] == "طلي"

    # The candidate is only proposed for review.
    assert item["candidate_text"] == "طلعي"

    # No corrected lyric field may be generated.
    assert "corrected_text" not in item
    assert "final_text" not in item

    assert (
        result["policy"]
        == "human_review_only_no_auto_correction"
    )

    print("TEST 10: No Auto Correction - PASS")


if __name__ == "__main__":
    test_build()
    test_review_candidate_is_queued()
    test_original_is_never_queued()
    test_negative_margin_is_not_queued()
    test_single_evidence_can_be_reviewed()
    test_two_evidence_has_higher_priority()
    test_recommendation_is_queued()
    test_strong_correction_is_queued()
    test_output_structure()
    test_no_auto_correction()

    print("STATUS: PASS")