"""
PhoenixVoiceEngine
Stable Pitch Center Analyzer V1.0.2
"""

from src.maqam.stable_pitch_center_analyzer import StablePitchCenterAnalyzer


def hz_from_midi(midi):
    return 440.0 * 2 ** ((midi - 69.0) / 12.0)


def make_stable_data():
    events = []
    # G with a slow small vibrato: should remain one stable region.
    for i in range(40):
        cents = 15.0 if i % 2 == 0 else -15.0
        events.append({
            "start_time": i * 0.02,
            "pitch_hz": hz_from_midi(55.0 + cents / 100.0),
        })

    # Slide/movement: should break the region.
    for i in range(12):
        midi = 55.0 + i * 0.5
        events.append({
            "start_time": 0.8 + i * 0.02,
            "pitch_hz": hz_from_midi(midi),
        })

    # A# stable center.
    for i in range(30):
        cents = -10.0 if i % 2 == 0 else 5.0
        events.append({
            "start_time": 1.2 + i * 0.02,
            "pitch_hz": hz_from_midi(58.0 + cents / 100.0),
        })

    return {"events": events}


def test_build():
    assert StablePitchCenterAnalyzer.PATCH_VERSION == "1.0.2"


def test_temporal_regions_detected():
    r = StablePitchCenterAnalyzer(
        min_samples=6,
        min_region_duration=0.10,
        max_step_cents=35,
        max_spread_cents=30,
        min_stability_ratio=0.20,
    ).analyze(make_stable_data())
    assert len(r["evidence"]["stable_regions"]) >= 2


def test_centers_detected():
    r = StablePitchCenterAnalyzer(
        min_samples=6,
        min_region_duration=0.10,
        max_step_cents=35,
        max_spread_cents=30,
        min_stability_ratio=0.20,
    ).analyze(make_stable_data())
    names = {x["pitch_class_name"] for x in r["evidence"]["stable_pitch_centers"]}
    assert "G" in names
    assert "A#" in names


def test_vibrato_is_not_automatic_movement():
    r = StablePitchCenterAnalyzer(
        min_samples=6,
        min_region_duration=0.10,
        max_step_cents=35,
        max_spread_cents=30,
        min_stability_ratio=0.20,
    ).analyze(make_stable_data())
    g_regions = [
        x for x in r["evidence"]["stable_regions"]
        if x["pitch_class_name"] == "G"
    ]
    assert g_regions


def test_no_source_correction():
    r = StablePitchCenterAnalyzer(
        min_samples=6,
        min_region_duration=0.10,
    ).analyze(make_stable_data())
    assert r["analysis"]["raw_pitch_preserved"] is True
    assert r["analysis"]["timing_preserved"] is True
    assert r["analysis"]["no_auto_correction"] is True
    assert r["analysis"]["no_maqam_decision"] is True


def test_octave_boundary():
    r = StablePitchCenterAnalyzer(
        min_samples=1,
        min_region_duration=0.01,
        max_step_cents=35,
    ).analyze(
        {
            "events": [
                {"start_time": 0.0, "midi_note": 67},
                {"start_time": 0.1, "midi_note": 67},
            ]
        },
        tonic_pitch_class=7,
    )
    assert all(
        x["relative_12tet"] != 12
        for x in r["evidence"]["tonic_relative_stable_centers"]
    )


def test_midi_only():
    r = StablePitchCenterAnalyzer(
        min_samples=1,
        min_region_duration=0.01,
        max_step_cents=35,
    ).analyze(
        {
            "events": [
                {"start_time": 0.0, "midi_note": 55},
                {"start_time": 0.1, "midi_note": 55},
            ]
        }
    )
    assert r["input"]["midi_sample_count"] == 2


def test_evidence_only():
    r = StablePitchCenterAnalyzer().analyze(make_stable_data())
    assert r["decision"] == {
        "status": "EVIDENCE_ONLY",
        "maqam": None,
        "jins": None,
        "confidence": None,
    }


def run():
    print("PhoenixVoiceEngine")
    print("Stable Pitch Center Analyzer V1.0.2")
    print("=" * 60)

    tests = [
        test_build,
        test_temporal_regions_detected,
        test_centers_detected,
        test_vibrato_is_not_automatic_movement,
        test_no_source_correction,
        test_octave_boundary,
        test_midi_only,
        test_evidence_only,
    ]

    for i, fn in enumerate(tests, 1):
        fn()
        print(f"TEST {i}: {fn.__name__} - PASS")

    print("=" * 60)
    print("STATUS: PASS")


if __name__ == "__main__":
    run()
