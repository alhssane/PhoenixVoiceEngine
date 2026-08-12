"""
PhoenixVoiceEngine
Raw Pitch Jins Evidence Analyzer V1.0
"""

from src.maqam.raw_pitch_jins_evidence_analyzer import (
    RawPitchJinsEvidenceAnalyzer,
)


def make_data():
    return {
        "events": [
            {
                "event_index": 1,
                "timing": {"start_time": 0.0},
                "melody": {
                    "midi_note": 55,
                    "pitch_hz": 195.9977,
                },
            },
            {
                "event_index": 2,
                "timing": {"start_time": 1.0},
                "melody": {
                    "midi_note": 57,
                    "pitch_hz": 220.0,
                },
            },
            {
                "event_index": 3,
                "timing": {"start_time": 2.0},
                "melody": {
                    "midi_note": 59,
                    "pitch_hz": 246.9417,
                },
            },
        ]
    }


def test_build():
    assert RawPitchJinsEvidenceAnalyzer.PATCH_VERSION == "1.0.0"


def test_recursive_extraction():
    r = RawPitchJinsEvidenceAnalyzer().analyze(make_data())
    assert r["input"]["sample_count"] == 3


def test_raw_hz_detection():
    r = RawPitchJinsEvidenceAnalyzer().analyze(make_data())
    assert r["input"]["raw_hz_sample_count"] == 3
    assert r["evidence"]["microtonal"]["available"] is True


def test_microtonal_evidence_only():
    r = RawPitchJinsEvidenceAnalyzer().analyze(make_data())
    assert r["decision"]["status"] == "EVIDENCE_ONLY"
    assert r["decision"]["maqam"] is None
    assert r["decision"]["jins"] is None


def test_tonic_relative_bins():
    r = RawPitchJinsEvidenceAnalyzer(
        tonic_pitch_class=7
    ).analyze(make_data())

    assert r["evidence"]["tonic_relative"]["available"] is True
    assert r["evidence"]["tonic_relative"]["sample_count"] == 3


def test_midi_only_protection():
    data = {
        "events": [
            {"melody": {"midi_note": 55}},
            {"melody": {"midi_note": 57}},
        ]
    }
    r = RawPitchJinsEvidenceAnalyzer().analyze(data)
    assert r["input"]["raw_hz_sample_count"] == 0
    assert r["evidence"]["microtonal"]["available"] is False
    assert r["evidence"]["microtonal"]["reason"] == "NO_RAW_HZ_EVIDENCE"


def test_no_correction():
    r = RawPitchJinsEvidenceAnalyzer().analyze(make_data())
    assert r["analysis"]["raw_pitch_preserved"] is True
    assert r["analysis"]["timing_preserved"] is True
    assert r["analysis"]["no_auto_correction"] is True
    assert r["analysis"]["no_maqam_decision"] is True


def run():
    print("PhoenixVoiceEngine")
    print("Raw Pitch Jins Evidence Analyzer V1.0")
    print("=" * 60)

    tests = [
        test_build,
        test_recursive_extraction,
        test_raw_hz_detection,
        test_microtonal_evidence_only,
        test_tonic_relative_bins,
        test_midi_only_protection,
        test_no_correction,
    ]

    for i, fn in enumerate(tests, 1):
        fn()
        print(f"TEST {i}: {fn.__name__} - PASS")

    print("=" * 60)
    print("STATUS: PASS")


if __name__ == "__main__":
    run()
