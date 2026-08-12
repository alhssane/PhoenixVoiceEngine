from src.maqam.tonic_relative_microtonal_evidence import (
    TonicRelativeMicrotonalEvidence,
)


def make_analyzer():
    return TonicRelativeMicrotonalEvidence()


def make_stable_data():
    return {
        "evidence": {
            "stable_pitch_centers": [
                {
                    "pitch_class": 7,
                    "pitch_class_name": "G",
                    "region_count": 20,
                    "total_duration": 10.0,
                    "sample_count": 1000,
                    "raw_hz_sample_count": 900,
                    "center_cents": -10.0,
                    "mean_stability_score": 0.80,
                },
                {
                    "pitch_class": 10,
                    "pitch_class_name": "A#",
                    "region_count": 15,
                    "total_duration": 8.0,
                    "sample_count": 800,
                    "raw_hz_sample_count": 700,
                    "center_cents": -8.0,
                    "mean_stability_score": 0.75,
                },
                {
                    "pitch_class": 0,
                    "pitch_class_name": "C",
                    "region_count": 15,
                    "total_duration": 8.0,
                    "sample_count": 800,
                    "raw_hz_sample_count": 700,
                    "center_cents": -12.0,
                    "mean_stability_score": 0.75,
                },
            ]
        }
    }


def test_build():
    assert (
        TonicRelativeMicrotonalEvidence.VERSION
        == "1.0.0"
    )

    assert (
        TonicRelativeMicrotonalEvidence.FEATURE_VERSION
        == "1.0.0"
    )

    assert (
        TonicRelativeMicrotonalEvidence.PATCH_VERSION
        == "1.0.0"
    )


def test_circular_cents():
    e = make_analyzer()

    assert e._circular_cents(0) == 0
    assert e._circular_cents(49) == 49
    assert e._circular_cents(51) == -49
    assert e._circular_cents(100) == 0
    assert e._circular_cents(-51) == 49


def test_relative_12tet():
    e = make_analyzer()

    # G tonic
    assert (
        e._relative_12tet(7, 7)
        == 0
    )

    assert (
        e._relative_12tet(7, 8)
        == 1
    )

    assert (
        e._relative_12tet(7, 10)
        == 3
    )

    assert (
        e._relative_12tet(7, 0)
        == 5
    )


def test_expected_cents():
    e = make_analyzer()

    assert (
        e._expected_cents(7, 7)
        == 0
    )

    assert (
        e._expected_cents(7, 10)
        == 300
    )

    assert (
        e._expected_cents(7, 0)
        == 500
    )


def test_extract_stable_centers():
    e = make_analyzer()

    centers = e._extract_stable_centers(
        make_stable_data()
    )

    assert len(centers) == 3
    assert centers[0]["pitch_class"] == 7
    assert centers[1]["pitch_class"] == 10


def test_relative_center():
    e = make_analyzer()

    center = {
        "pitch_class": 10,
        "pitch_class_name": "A#",
        "center_cents": -8.0,
        "region_count": 10,
        "total_duration": 5.0,
        "sample_count": 500,
        "raw_hz_sample_count": 450,
        "mean_stability_score": 0.8,
    }

    result = e._relative_center(
        tonic_pitch_class=7,
        center=center,
    )

    assert result["relative_12tet"] == 3
    assert (
        result["expected_relative_cents"]
        == 300
    )

    assert (
        result["measured_center_cents"]
        == -8.0
    )

    assert (
        result["observed_relative_cents"]
        == 292.0
    )


def test_candidate_generation():
    e = make_analyzer()

    r = e.analyze(
        make_stable_data(),
        candidates=[7, 0],
    )

    assert len(
        r["ranking"]["candidates"]
    ) == 2


def test_score_range():
    e = make_analyzer()

    r = e.analyze(
        make_stable_data(),
        candidates=[7, 0],
    )

    for candidate in r["ranking"]["candidates"]:
        assert (
            0.0
            <= candidate["score"]
            <= 1.0
        )


def test_relative_evidence_present():
    e = make_analyzer()

    r = e.analyze(
        make_stable_data(),
        candidates=[7, 0],
    )

    for candidate in r["ranking"]["candidates"]:
        assert (
            "relative_centers"
            in candidate
        )

        assert (
            len(
                candidate[
                    "relative_centers"
                ]
            )
            == 3
        )


def test_evidence_only():
    e = make_analyzer()

    r = e.analyze(
        make_stable_data(),
        candidates=[7, 0],
    )

    assert (
        r["decision"]["status"]
        == "EVIDENCE_ONLY"
    )

    assert (
        r["decision"][
            "tonic_pitch_class"
        ]
        is None
    )

    assert (
        r["decision"]["tonic_name"]
        is None
    )

    assert (
        r["decision"]["maqam"]
        is None
    )

    assert (
        r["decision"]["jins"]
        is None
    )


def test_no_pitch_correction():
    e = make_analyzer()

    r = e.analyze(
        make_stable_data(),
        candidates=[7, 0],
    )

    protection = r[
        "protection"
    ]

    assert (
        protection[
            "source_pitch_modified"
        ]
        is False
    )

    assert (
        protection[
            "source_timing_modified"
        ]
        is False
    )

    assert (
        protection[
            "source_performance_modified"
        ]
        is False
    )


def run():
    print("PhoenixVoiceEngine")
    print(
        "Tonic Relative Microtonal "
        "Evidence V1.0"
    )
    print("=" * 60)

    tests = [
        test_build,
        test_circular_cents,
        test_relative_12tet,
        test_expected_cents,
        test_extract_stable_centers,
        test_relative_center,
        test_candidate_generation,
        test_score_range,
        test_relative_evidence_present,
        test_evidence_only,
        test_no_pitch_correction,
    ]

    for i, fn in enumerate(
        tests,
        1,
    ):
        fn()
        print(
            f"TEST {i}: "
            f"{fn.__name__} - PASS"
        )

    print("=" * 60)
    print("STATUS: PASS")


if __name__ == "__main__":
    run()