from __future__ import annotations

import json
import tempfile
from pathlib import Path

from src.ui.lyric_review_ui import LyricReviewUI


def make_queue(path: Path) -> None:
    data = {
        "version": "1.0.1",
        "queue_count": 2,
        "priority_counts": {
            "HIGH": 1,
            "MEDIUM": 1,
            "LOW": 0,
        },
        "decision_counts": {
            "REVIEW_CANDIDATE": 2,
            "RECOMMEND_CORRECTION": 0,
            "STRONG_CORRECTION": 0,
        },
        "queue": [
            {
                "queue_position": 1,
                "original_text": "كلمة",
                "candidate_text": "بديل",
                "priority": "HIGH",
                "decision": "REVIEW_CANDIDATE",
                "margin_vs_original": 15.0,
                "independent_support_count": 2,
                "original_confidence": 65.0,
                "start_time": 10.0,
                "end_time": 11.0,
                "candidates": [
                    {
                        "text": "بديل",
                        "confidence": 90.0,
                        "fusion": {
                            "candidate_total_score": 80.0,
                            "margin_vs_original": 15.0,
                            "independent_support_count": 2,
                            "decision": "REVIEW_CANDIDATE",
                        },
                    }
                ],
            },
            {
                "queue_position": 2,
                "original_text": "ثانية",
                "candidate_text": "بديل2",
                "priority": "MEDIUM",
                "decision": "REVIEW_CANDIDATE",
                "margin_vs_original": 10.0,
                "independent_support_count": 1,
                "original_confidence": 70.0,
                "start_time": 20.0,
                "end_time": 21.0,
                "candidates": [
                    {
                        "text": "بديل2",
                        "confidence": 88.0,
                        "fusion": {
                            "candidate_total_score": 78.0,
                            "margin_vs_original": 10.0,
                            "independent_support_count": 1,
                            "decision": "REVIEW_CANDIDATE",
                        },
                    }
                ],
            },
        ],
    }

    path.write_text(
        json.dumps(
            data,
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )


def test_build():

    with tempfile.TemporaryDirectory() as tmp:

        root = Path(tmp)

        queue = root / "queue.json"
        audio = root / "audio.wav"
        session = root / "session.json"
        final = root / "final.json"

        make_queue(queue)

        ui = LyricReviewUI(
            queue_path=queue,
            audio_path=audio,
            output_session_path=session,
            output_final_path=final,
        )

        assert ui.VERSION == "1.0.0"
        assert len(ui.queue) == 2
        assert ui.session is not None

        print("TEST 1: Build - PASS")


def test_item_info():

    with tempfile.TemporaryDirectory() as tmp:

        root = Path(tmp)

        queue = root / "queue.json"
        make_queue(queue)

        ui = LyricReviewUI(
            queue_path=queue,
            audio_path=root / "audio.wav",
            output_session_path=root / "session.json",
            output_final_path=root / "final.json",
        )

        text = ui._item_info()

        assert "كلمة" in text
        assert "بديل" in text
        assert "HIGH" in text
        assert "65.00%" in text

        print("TEST 2: Item Info - PASS")


def test_candidate_lines():

    with tempfile.TemporaryDirectory() as tmp:

        root = Path(tmp)

        queue = root / "queue.json"
        make_queue(queue)

        ui = LyricReviewUI(
            queue_path=queue,
            audio_path=root / "audio.wav",
            output_session_path=root / "session.json",
            output_final_path=root / "final.json",
        )

        item = ui._current_item()

        text = ui._candidate_lines(item)

        assert "بديل" in text
        assert "90.00%" in text
        assert "80.00" in text
        assert "supports=2" in text

        print("TEST 3: Candidate Display - PASS")


def test_status():

    with tempfile.TemporaryDirectory() as tmp:

        root = Path(tmp)

        queue = root / "queue.json"
        make_queue(queue)

        ui = LyricReviewUI(
            queue_path=queue,
            audio_path=root / "audio.wav",
            output_session_path=root / "session.json",
            output_final_path=root / "final.json",
        )

        status = ui._status_text()

        assert "1 / 2" in status

        print("TEST 4: Status - PASS")


def test_navigation():

    with tempfile.TemporaryDirectory() as tmp:

        root = Path(tmp)

        queue = root / "queue.json"
        make_queue(queue)

        ui = LyricReviewUI(
            queue_path=queue,
            audio_path=root / "audio.wav",
            output_session_path=root / "session.json",
            output_final_path=root / "final.json",
        )

        assert ui._current_index() == 0

        ui.next()

        assert ui._current_index() == 1

        ui.previous()

        assert ui._current_index() == 0

        print("TEST 5: Navigation - PASS")


def test_ui_actions():

    with tempfile.TemporaryDirectory() as tmp:

        root = Path(tmp)

        queue = root / "queue.json"
        make_queue(queue)

        ui = LyricReviewUI(
            queue_path=queue,
            audio_path=root / "audio.wav",
            output_session_path=root / "session.json",
            output_final_path=root / "final.json",
        )

        ui.keep_original()

        assert ui._current_index() == 1

        print("TEST 6: Keep Original - PASS")


def test_save_session():

    with tempfile.TemporaryDirectory() as tmp:

        root = Path(tmp)

        queue = root / "queue.json"
        session_path = root / "session.json"

        make_queue(queue)

        ui = LyricReviewUI(
            queue_path=queue,
            audio_path=root / "audio.wav",
            output_session_path=session_path,
            output_final_path=root / "final.json",
        )

        ui.save_session()

        assert session_path.exists()

        data = json.loads(
            session_path.read_text(
                encoding="utf-8"
            )
        )

        assert isinstance(data, dict)

        print("TEST 7: Save Session - PASS")


def test_gradio_build():

    with tempfile.TemporaryDirectory() as tmp:

        root = Path(tmp)

        queue = root / "queue.json"
        make_queue(queue)

        ui = LyricReviewUI(
            queue_path=queue,
            audio_path=root / "audio.wav",
            output_session_path=root / "session.json",
            output_final_path=root / "final.json",
        )

        app = ui.build()

        assert app is not None

        print("TEST 8: Gradio Build - PASS")


if __name__ == "__main__":

    print("=" * 60)
    print("PhoenixVoiceEngine")
    print("Lyric Human Review Interface V1.0")
    print("=" * 60)

    test_build()
    test_item_info()
    test_candidate_lines()
    test_status()
    test_navigation()
    test_ui_actions()
    test_save_session()
    test_gradio_build()

    print("=" * 60)
    print("STATUS: PASS")
    print("=" * 60)