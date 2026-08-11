from __future__ import annotations

import json
import tempfile
from pathlib import Path

from src.analyzer.lyric_finalizer import LyricFinalizer


def make_session() -> dict:

    return {
        "version": "1.0.0",
        "queue": [
            {
                "queue_position": 1,
                "original_text": "كلمة",
                "candidate_text": "بديل",
                "review_decision": "KEEP_ORIGINAL",
                "start_time": 1.0,
                "end_time": 2.0,
            },
            {
                "queue_position": 2,
                "original_text": "ثانية",
                "candidate_text": "بديل2",
                "review_decision": "ACCEPT_CANDIDATE",
                "accepted_candidate": "بديل2",
                "start_time": 2.0,
                "end_time": 3.0,
            },
            {
                "queue_position": 3,
                "original_text": "ثالثة",
                "candidate_text": "بديل3",
                "review_decision": "CUSTOM_CORRECTION",
                "custom_correction": "التصحيح",
                "start_time": 3.0,
                "end_time": 4.0,
            },
            {
                "queue_position": 4,
                "original_text": "رابعة",
                "candidate_text": "بديل4",
                "review_decision": "SKIP",
                "start_time": 4.0,
                "end_time": 5.0,
            },
        ],
    }


def test_build():

    engine = LyricFinalizer()

    assert engine.VERSION == "1.0.0"

    print(
        "TEST 1: Build - PASS"
    )


def test_original_preservation():

    engine = LyricFinalizer()

    session = make_session()

    result = engine.finalize(
        session
    )

    assert (
        result["items"][0]["final_text"]
        == "كلمة"
    )

    print(
        "TEST 2: Original Preservation - PASS"
    )


def test_candidate_acceptance():

    engine = LyricFinalizer()

    result = engine.finalize(
        make_session()
    )

    assert (
        result["items"][1]["final_text"]
        == "بديل2"
    )

    print(
        "TEST 3: Candidate Acceptance - PASS"
    )


def test_custom_correction():

    engine = LyricFinalizer()

    result = engine.finalize(
        make_session()
    )

    assert (
        result["items"][2]["final_text"]
        == "التصحيح"
    )

    print(
        "TEST 4: Custom Correction - PASS"
    )


def test_skip_preserves_original():

    engine = LyricFinalizer()

    result = engine.finalize(
        make_session()
    )

    assert (
        result["items"][3]["final_text"]
        == "رابعة"
    )

    print(
        "TEST 5: Skip Protection - PASS"
    )


def test_order_preservation():

    engine = LyricFinalizer()

    result = engine.finalize(
        make_session()
    )

    texts = [
        item["final_text"]
        for item in result["items"]
    ]

    assert texts == [
        "كلمة",
        "بديل2",
        "التصحيح",
        "رابعة",
    ]

    print(
        "TEST 6: Final Order Preservation - PASS"
    )


def test_timing_preservation():

    engine = LyricFinalizer()

    result = engine.finalize(
        make_session()
    )

    assert (
        result["items"][0]["start_time"]
        == 1.0
    )

    assert (
        result["items"][0]["end_time"]
        == 2.0
    )

    assert (
        result["items"][3]["start_time"]
        == 4.0
    )

    print(
        "TEST 7: Timing Preservation - PASS"
    )


def test_text_export():

    engine = LyricFinalizer()

    result = engine.finalize(
        make_session()
    )

    text = engine.to_text(
        result
    )

    assert "كلمة" in text
    assert "بديل2" in text
    assert "التصحيح" in text
    assert "رابعة" in text

    print(
        "TEST 8: TXT Export - PASS"
    )


def test_srt_export():

    engine = LyricFinalizer()

    result = engine.finalize(
        make_session()
    )

    srt = engine.to_srt(
        result
    )

    assert "00:00:01,000" in srt
    assert "00:00:02,000" in srt
    assert "كلمة" in srt

    print(
        "TEST 9: SRT Export - PASS"
    )


def test_vtt_export():

    engine = LyricFinalizer()

    result = engine.finalize(
        make_session()
    )

    vtt = engine.to_vtt(
        result
    )

    assert vtt.startswith(
        "WEBVTT"
    )

    assert (
        "00:00:01.000 --> "
        "00:00:02.000"
        in vtt
    )

    assert "كلمة" in vtt

    print(
        "TEST 10: VTT Export - PASS"
    )


def test_output_structure():

    engine = LyricFinalizer()

    result = engine.finalize(
        make_session()
    )

    assert result["version"] == "1.0.0"
    assert result["source"] == (
        "LyricReviewSession"
    )
    assert result["item_count"] == 4
    assert len(result["items"]) == 4

    print(
        "TEST 11: Output Structure - PASS"
    )


def test_invalid_decision_protection():

    engine = LyricFinalizer()

    session = make_session()

    session["queue"][0][
        "review_decision"
    ] = "AUTO_CORRECT"

    try:
        engine.finalize(
            session
        )

    except ValueError:
        print(
            "TEST 12: Invalid Decision Protection - PASS"
        )
        return

    raise AssertionError(
        "Invalid decision was accepted."
    )


def test_no_auto_correction():

    engine = LyricFinalizer()

    session = make_session()

    session["queue"][0][
        "original_text"
    ] = "الأصل"

    session["queue"][0][
        "candidate_text"
    ] = "تصحيح"

    result = engine.finalize(
        session
    )

    assert (
        result["items"][0]["final_text"]
        == "الأصل"
    )

    print(
        "TEST 13: No Auto Correction - PASS"
    )


def test_export_files():

    engine = LyricFinalizer()

    with tempfile.TemporaryDirectory() as tmp:

        root = Path(tmp)

        session_path = (
            root / "session.json"
        )

        output_dir = (
            root / "outputs"
        )

        session_path.write_text(
            json.dumps(
                make_session(),
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )

        result = engine.export(
            session_path,
            output_dir,
            "bender_final_lyrics",
        )

        assert (
            Path(result["json"]).exists()
        )

        assert (
            Path(result["txt"]).exists()
        )

        assert (
            Path(result["srt"]).exists()
        )

        assert (
            Path(result["vtt"]).exists()
        )

    print(
        "TEST 14: Export Files - PASS"
    )


if __name__ == "__main__":

    print("=" * 60)
    print(
        "PhoenixVoiceEngine"
    )
    print(
        "Lyric Finalization & Export V1.0"
    )
    print("=" * 60)

    test_build()
    test_original_preservation()
    test_candidate_acceptance()
    test_custom_correction()
    test_skip_preserves_original()
    test_order_preservation()
    test_timing_preservation()
    test_text_export()
    test_srt_export()
    test_vtt_export()
    test_output_structure()
    test_invalid_decision_protection()
    test_no_auto_correction()
    test_export_files()

    print("=" * 60)
    print("STATUS: PASS")
    print("=" * 60)