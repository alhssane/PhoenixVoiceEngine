"""Tests for PhoenixVoiceEngine LyricCandidateGenerator V1.1."""

from src.analyzer.lyric_candidate_generator import LyricCandidateGenerator


def synthetic_report():
    return {
        "segments": [
            {
                "words": [
                    {
                        "text": "الغزال",
                        "start_time": 0.0,
                        "end_time": 0.8,
                        "confidence": 99.0,
                    },
                    {
                        "text": "السماء",
                        "start_time": 1.0,
                        "end_time": 1.8,
                        "confidence": 65.0,
                    },
                    {
                        "text": "زفتك",
                        "start_time": 2.0,
                        "end_time": 2.7,
                        "confidence": 100.0,
                    },
                ]
            }
        ]
    }


def fake_transcriber(**kwargs):
    if kwargs["beam_size"] == 5:
        return [
            {
                "text": "النسمة",
                "words": [
                    {
                        "word": "النسمة",
                        "start": 1.05,
                        "end": 1.75,
                        "probability": 0.93,
                    }
                ],
            }
        ]

    return [
        {
            "text": "السماء",
            "words": [
                {
                    "word": "السماء",
                    "start": 1.02,
                    "end": 1.78,
                    "probability": 0.68,
                }
            ],
        }
    ]


def fake_bad_segment_transcriber(**kwargs):
    # The whole segment is outside the target word interval.
    return [
        {
            "text": "اشتركوا في القناة",
            "words": [
                {"word": "اشتركوا", "start": 0.0, "end": 0.3, "probability": 0.95},
                {"word": "في", "start": 0.3, "end": 0.5, "probability": 0.95},
                {"word": "القناة", "start": 0.5, "end": 0.8, "probability": 0.95},
            ],
        }
    ]


def test_suspicious_detection():
    engine = LyricCandidateGenerator(
        transcriber=fake_transcriber,
        suspicious_confidence=82.0,
    )
    words = engine.suspicious_words(synthetic_report())

    assert len(words) == 1
    assert words[0]["text"] == "السماء"
    print("TEST 1: Suspicious Word Detection - PASS")


def test_target_word_alignment():
    engine = LyricCandidateGenerator(
        transcriber=fake_transcriber,
        suspicious_confidence=82.0,
    )
    report = engine.generate_for_report("synthetic.wav", synthetic_report())

    candidates = report["reports"][0]["candidates"]
    texts = [item["text"] for item in candidates]

    assert "النسمة" in texts
    assert "السماء" in texts
    print("TEST 2: Target Word Alignment - PASS")


def test_multword_segment_not_misattributed():
    engine = LyricCandidateGenerator(
        transcriber=fake_bad_segment_transcriber,
        suspicious_confidence=82.0,
    )
    report = engine.generate_for_report("synthetic.wav", synthetic_report())

    candidates = report["reports"][0]["candidates"]
    non_original = [
        item for item in candidates
        if item["source"] != "original-asr"
    ]

    assert non_original == []
    print("TEST 3: Multi-word Alignment Protection - PASS")


def test_original_preserved():
    engine = LyricCandidateGenerator(
        transcriber=fake_transcriber,
        suspicious_confidence=82.0,
    )
    report = engine.generate_for_report("synthetic.wav", synthetic_report())
    item = report["reports"][0]

    assert item["original_text"] == "السماء"
    assert any(
        c["text"] == "السماء"
        and c["source"] == "original-asr"
        for c in item["candidates"]
    )
    print("TEST 4: Original Preservation - PASS")


def test_timing_preserved():
    engine = LyricCandidateGenerator(
        transcriber=fake_transcriber,
        suspicious_confidence=82.0,
    )
    report = engine.generate_for_report("synthetic.wav", synthetic_report())
    item = report["reports"][0]

    assert item["start_time"] == 1.0
    assert item["end_time"] == 1.8
    print("TEST 5: Timing Preservation - PASS")


def test_high_confidence_not_redecoded():
    calls = []

    def recorder(**kwargs):
        calls.append(kwargs)
        return []

    engine = LyricCandidateGenerator(
        transcriber=recorder,
        suspicious_confidence=82.0,
    )
    report = engine.generate_for_report("synthetic.wav", synthetic_report())

    assert len(calls) == 2
    assert report["reports"][0]["suspicious"] is True
    print("TEST 6: High Confidence Protection - PASS")


if __name__ == "__main__":
    test_suspicious_detection()
    test_target_word_alignment()
    test_multword_segment_not_misattributed()
    test_original_preserved()
    test_timing_preserved()
    test_high_confidence_not_redecoded()
    print("STATUS: PASS")