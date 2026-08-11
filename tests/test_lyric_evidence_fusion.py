"""Tests for Lyric Evidence Fusion V1.1.1 Review Calibration."""

from src.analyzer.lyric_evidence_fusion import LyricEvidenceFusion


# ---------------------------------------------------------------------------
# Shared test data
# ---------------------------------------------------------------------------

def base():
    return {
        "reports": [{
            "word_index": 1,
            "original_text": "تحملها",
            "original_confidence": 74.0,
            "start_time": 1.0,
            "end_time": 2.0,

            "candidates": [
                {
                    "text": "تحملها",
                    "confidence": 74.0,
                    "evidence": {
                        "asr_confidence": 74.0,
                        "confidence_gain": 0.0,
                        "repetition_support": 0.0,
                        "total_score": 25.0,
                    },
                },

                {
                    "text": "كافك",
                    "confidence": 96.0,
                    "evidence": {
                        "asr_confidence": 96.0,
                        "confidence_gain": 22.0,
                        "repetition_support": 0.0,
                        "total_score": 90.0,
                    },
                },
            ],
        }]
    }


def ctx_original_strong():
    return {
        "reports": [{
            "word_index": 1,

            "context_candidates": [
                {
                    "text": "تحملها",
                    "context": {
                        "total_score": 25.0,
                        "repeated_context_score": 0.0,
                        "phrase_support_score": 0.0,
                        "position_score": 0.0,
                    },
                },

                {
                    "text": "كافك",
                    "context": {
                        "total_score": 40.0,
                        "repeated_context_score": 0.0,
                        "phrase_support_score": 0.0,
                        "position_score": 0.0,
                    },
                },
            ],
        }]
    }


# ---------------------------------------------------------------------------
# TEST 1
# ---------------------------------------------------------------------------

def test_build():
    assert LyricEvidenceFusion.VERSION == "1.1.1"

    print("TEST 1: Build - PASS")


# ---------------------------------------------------------------------------
# TEST 2
#
# Positive margin + only one independent evidence family
# must produce REVIEW_CANDIDATE.
# ---------------------------------------------------------------------------

def test_positive_margin_with_single_support_becomes_review():

    result = LyricEvidenceFusion().analyze(
        base(),
        ctx_original_strong(),
    )

    report = result["reports"][0]

    candidate = next(
        c
        for c in report["candidates"]
        if c["text"] == "كافك"
    )

    assert candidate["fusion"]["margin_vs_original"] > 0

    assert candidate["fusion"]["independent_support_count"] == 1

    assert candidate["fusion"]["decision"] == "REVIEW_CANDIDATE"

    assert report["recommendation"] == "REVIEW_CANDIDATE"

    assert report["recommended_candidate"] is None

    print("TEST 2: Positive Margin Review Calibration - PASS")


# ---------------------------------------------------------------------------
# TEST 3
#
# Negative margin must always protect the original.
# ---------------------------------------------------------------------------

def test_negative_margin_keeps_original():

    scored = base()

    candidate = scored["reports"][0]["candidates"][1]

    # Completely weaken the alternative candidate.
    #
    # Important:
    # total_score alone is NOT enough because the Fusion engine
    # also considers ASR confidence and confidence gain.
    candidate["evidence"]["total_score"] = 10.0
    candidate["evidence"]["asr_confidence"] = 10.0
    candidate["evidence"]["confidence_gain"] = 0.0
    candidate["evidence"]["repetition_support"] = 0.0

    context = ctx_original_strong()

    # Remove contextual support from the alternative candidate.
    context["reports"][0]["context_candidates"][1]["context"] = {
        "total_score": 5.0,
        "repeated_context_score": 0.0,
        "phrase_support_score": 0.0,
        "position_score": 0.0,
    }

    result = LyricEvidenceFusion().analyze(
        scored,
        context,
    )

    report = result["reports"][0]

    candidate = next(
        c
        for c in report["candidates"]
        if c["text"] == "كافك"
    )

    assert candidate["fusion"]["margin_vs_original"] <= 0

    assert candidate["fusion"]["decision"] == "KEEP_ORIGINAL"

    assert report["recommendation"] == "KEEP_ORIGINAL"

    assert report["recommended_candidate"] is None

    print("TEST 3: Negative Margin Protection - PASS")


# ---------------------------------------------------------------------------
# TEST 4
#
# Strong multi-evidence case.
#
# The alternative candidate receives:
#
#   1. Strong acoustic evidence
#   2. Strong context evidence
#   3. Strong repetition evidence
#   4. Strong phrase evidence
#   5. Strong position evidence
#
# Therefore the engine should be allowed to recommend it.
# ---------------------------------------------------------------------------

def test_two_evidence_families_can_recommend():

    scored = base()

    candidate = scored["reports"][0]["candidates"][1]

    # Strong acoustic / candidate evidence.
    candidate["evidence"]["total_score"] = 100.0
    candidate["evidence"]["asr_confidence"] = 100.0
    candidate["evidence"]["confidence_gain"] = 30.0
    candidate["evidence"]["repetition_support"] = 100.0

    context = ctx_original_strong()

    # Strong independent contextual evidence.
    context["reports"][0]["context_candidates"][1]["context"] = {
        "total_score": 100.0,
        "repeated_context_score": 100.0,
        "phrase_support_score": 100.0,
        "position_score": 100.0,
    }

    result = LyricEvidenceFusion().analyze(
        scored,
        context,
    )

    report = result["reports"][0]

    candidate = next(
        c
        for c in report["candidates"]
        if c["text"] == "كافك"
    )

    # Must have multiple independent evidence families.
    assert candidate["fusion"]["independent_support_count"] >= 2

    # Candidate must clearly beat the original.
    assert candidate["fusion"]["margin_vs_original"] > 0

    # The decision must be a valid correction recommendation.
    assert candidate["fusion"]["decision"] in {
        "RECOMMEND_CORRECTION",
        "STRONG_CORRECTION",
    }

    # Report-level recommendation must match.
    assert report["recommendation"] in {
        "RECOMMEND_CORRECTION",
        "STRONG_CORRECTION",
    }

    assert report["recommended_candidate"] == "كافك"

    print("TEST 4: Multi-Evidence Recommendation - PASS")


# ---------------------------------------------------------------------------
# TEST 5
#
# The original ASR word can never become a correction candidate.
# ---------------------------------------------------------------------------

def test_original_can_never_be_recommended_as_correction():

    result = LyricEvidenceFusion().analyze(
        base(),
        ctx_original_strong(),
    )

    report = result["reports"][0]

    original = next(
        c
        for c in report["candidates"]
        if c["text"] == "تحملها"
    )

    assert original["fusion"]["decision"] == "KEEP_ORIGINAL"

    assert report["recommended_candidate"] is None

    print("TEST 5: Original Preservation - PASS")


# ---------------------------------------------------------------------------
# TEST 6
#
# Fusion is an evidence / recommendation layer only.
# It must never modify the lyric text automatically.
# ---------------------------------------------------------------------------

def test_no_auto_correction():

    scored = base()

    candidate = scored["reports"][0]["candidates"][1]

    candidate["evidence"]["total_score"] = 99.0
    candidate["evidence"]["asr_confidence"] = 99.0
    candidate["evidence"]["confidence_gain"] = 30.0
    candidate["evidence"]["repetition_support"] = 100.0

    context = ctx_original_strong()

    context["reports"][0]["context_candidates"][1]["context"] = {
        "total_score": 100.0,
        "repeated_context_score": 100.0,
        "phrase_support_score": 100.0,
        "position_score": 100.0,
    }

    result = LyricEvidenceFusion().analyze(
        scored,
        context,
    )

    report = result["reports"][0]

    # There must never be an automatically corrected text field.
    assert "corrected_text" not in report

    # The engine may recommend a candidate,
    # but it must not alter the original text.
    assert report["recommended_candidate"] in {
        None,
        "كافك",
    }

    assert report["original_text"] == "تحملها"

    print("TEST 6: No Auto Correction - PASS")


# ---------------------------------------------------------------------------
# TEST 7
#
# Validate output structure.
# ---------------------------------------------------------------------------

def test_output_structure():

    result = LyricEvidenceFusion().analyze(
        base(),
        ctx_original_strong(),
    )

    assert result["version"] == "1.1.1"

    assert result["calibration"] == "review_calibration"

    assert result["mode"] == "comparative_decision_engine"

    assert result["policy"] == "evidence_only_no_auto_correction"

    assert "report_count" in result

    assert "reports" in result

    assert isinstance(result["reports"], list)

    assert len(result["reports"]) == 1

    report = result["reports"][0]

    required_report_fields = {
        "word_index",
        "original_text",
        "original_confidence",
        "start_time",
        "end_time",
        "original_fusion_score",
        "recommendation",
        "recommended_candidate",
        "candidates",
    }

    assert required_report_fields.issubset(
        report.keys()
    )

    assert isinstance(
        report["candidates"],
        list,
    )

    fusion = report["candidates"][0]["fusion"]

    required_fusion_fields = {
        "candidate_score",
        "candidate_acoustic_score",
        "confidence_gain",
        "context_score",
        "repeated_context_score",
        "phrase_support_score",
        "position_score",
        "independent_support_count",
        "candidate_total_score",
        "original_total_score",
        "margin_vs_original",
        "relative_margin",
        "decision",
        "reasons",
    }

    assert required_fusion_fields.issubset(
        fusion.keys()
    )

    print("TEST 7: Output Structure - PASS")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

if __name__ == "__main__":

    test_build()

    test_positive_margin_with_single_support_becomes_review()

    test_negative_margin_keeps_original()

    test_two_evidence_families_can_recommend()

    test_original_can_never_be_recommended_as_correction()

    test_no_auto_correction()

    test_output_structure()

    print("STATUS: PASS")