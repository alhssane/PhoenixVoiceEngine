from src.maqam.tonic_intervallic_relationship_analyzer import (
    TonicIntervallicRelationshipAnalyzer,
)


def make_analyzer():
    return TonicIntervallicRelationshipAnalyzer()


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
                    "center_cents": -17.0,
                    "mean_stability_score": 0.80,
                },
                {
                    "pitch_class": 10,
                    "pitch_class_name": "A#",
                    "region_count": 15,
                    "total_duration": 8.0,
                    "sample_count": 800,
                    "center_cents": -10.0,
                    "mean_stability_score": 0.75,
                },
                {
                    "pitch_class": 0,
                    "pitch_class_name": "C",
                    "region_count": 15,
                    "total_duration": 8.0,
                    "sample_count": 800,
                    "center_cents": -14.0,
                    "mean_stability_score": 0.75,
                },
            ]
        }
    }


def make_cadence_data():
    return {
        "evidence": {
            "stable_transitions": {
                "ranked_pairs": [
                    {
                        "source_pitch_class": 10,
                        "target_pitch_class": 7,
                        "count": 10,
                    },
                    {
                        "source_pitch_class": 0,
                        "target_pitch_class": 10,
                        "count": 8,
                    },
                    {
                        "source_pitch_class": 7,
                        "target_pitch_class": 7,
                        "count": 5,
                    },
                    {
                        "source_pitch_class": 2,
                        "target_pitch_class": 7,
                        "count": 4,
                    },
                ]
            }
        }
    }


def test_build():
    assert (
        TonicIntervallicRelationshipAnalyzer.VERSION
        == "1.0.0"
    )

    assert (
        TonicIntervallicRelationshipAnalyzer.FEATURE_VERSION
        == "1.0.0"
    )

    assert (
        TonicIntervallicRelationshipAnalyzer.PATCH_VERSION
        == "1.0.0"
    )


def test_relative_interval():
    e = make_analyzer()

    assert (
        e._relative_interval(7, 7)
        == 0
    )

    assert (
        e._relative_interval(7, 8)
        == 1
    )

    assert (
        e._relative_interval(7, 10)
        == 3
    )

    assert (
        e._relative_interval(7, 0)
        == 5
    )


def test_extract_stable_centers():
    e = make_analyzer()

    centers = e._extract_stable_centers(
        make_stable_data()
    )

    assert len(centers) == 3

    assert (
        centers[0]["pitch_class"]
        == 7
    )

    assert (
        centers[1]["pitch_class"]
        == 10
    )


def test_extract_transitions():
    e = make_analyzer()

    transitions = e._extract_transitions(
        make_cadence_data()
    )

    assert len(transitions) == 4

    assert (
        transitions[0][
            "source_pitch_class"
        ]
        == 10
    )

    assert (
        transitions[0][
            "target_pitch_class"
        ]
        == 7
    )


def test_stable_relationships():
    e = make_analyzer()

    centers = e._extract_stable_centers(
        make_stable_data()
    )

    result = e._stable_relationships(
        7,
        centers,
    )

    assert (
        result["coverage"]
        > 0
    )

    g = next(
        x
        for x in result["relationships"]
        if x["pitch_class"] == 7
    )

    assert (
        g["relative_interval"]
        == 0
    )

    a_sharp = next(
        x
        for x in result["relationships"]
        if x["pitch_class"] == 10
    )

    assert (
        a_sharp["relative_interval"]
        == 3
    )


def test_tonic_transition_evidence():
    e = make_analyzer()

    transitions = e._extract_transitions(
        make_cadence_data()
    )

    result = e._tonic_transition_evidence(
        7,
        transitions,
    )

    # A# -> G = 10
    # D  -> G = 4
    # G  -> G = 5
    # Self-transition also counts as an incoming
    # transition because its target is the tonic.
    # Total incoming = 19
    assert (
        result["incoming_count"]
        == 19
    )

    # G -> G = 5
    assert (
        result["outgoing_count"]
        == 5
    )

    # G -> G = 5
    assert (
        result["self_transition_count"]
        == 5
    )

    # Ratios must remain normalized.
    assert (
        0.0
        <= result["incoming_ratio"]
        <= 1.0
    )

    assert (
        0.0
        <= result["outgoing_ratio"]
        <= 1.0
    )

    assert (
        0.0
        <= result["self_ratio"]
        <= 1.0
    )

    # Score is intentionally allowed to reach 1.0
    # because the analyzer clamps evidence scores
    # to the [0, 1] range.
    assert (
        0.0
        <= result["score"]
        <= 1.0
    )


def test_candidate_generation():
    e = make_analyzer()

    result = e.analyze(
        make_stable_data(),
        make_cadence_data(),
        candidates=[7, 0],
    )

    assert (
        len(
            result["ranking"][
                "candidates"
            ]
        )
        == 2
    )


def test_components_present():
    e = make_analyzer()

    result = e.analyze(
        make_stable_data(),
        make_cadence_data(),
        candidates=[7, 0],
    )

    for candidate in result[
        "ranking"
    ]["candidates"]:

        assert (
            "pitch_recurrence"
            in candidate["components"]
        )

        assert (
            "tonic_transition"
            in candidate["components"]
        )

        assert (
            "stable_center_coverage"
            in candidate["components"]
        )

        assert (
            "relationship_availability"
            in candidate["components"]
        )


def test_score_range():
    e = make_analyzer()

    result = e.analyze(
        make_stable_data(),
        make_cadence_data(),
        candidates=[7, 0],
    )

    for candidate in result[
        "ranking"
    ]["candidates"]:

        assert (
            0.0
            <= candidate["score"]
            <= 1.0
        )


def test_margin():
    e = make_analyzer()

    result = e.analyze(
        make_stable_data(),
        make_cadence_data(),
        candidates=[7, 0],
    )

    assert (
        result["ranking"]["margin"]
        >= 0.0
    )


def test_evidence_only():
    e = make_analyzer()

    result = e.analyze(
        make_stable_data(),
        make_cadence_data(),
        candidates=[7, 0],
    )

    assert (
        result["decision"]["status"]
        == "EVIDENCE_ONLY"
    )

    assert (
        result["decision"][
            "tonic_pitch_class"
        ]
        is None
    )

    assert (
        result["decision"]["tonic_name"]
        is None
    )

    assert (
        result["decision"]["maqam"]
        is None
    )

    assert (
        result["decision"]["jins"]
        is None
    )


def test_protection():
    e = make_analyzer()

    result = e.analyze(
        make_stable_data(),
        make_cadence_data(),
        candidates=[7, 0],
    )

    protection = result[
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

    assert (
        protection[
            "tonic_decision_made"
        ]
        is False
    )

    assert (
        protection[
            "maqam_decision_made"
        ]
        is False
    )

    assert (
        protection[
            "jins_decision_made"
        ]
        is False
    )


def run():
    print(
        "PhoenixVoiceEngine"
    )

    print(
        "Tonic Intervallic Relationship "
        "Analyzer V1.0"
    )

    print(
        "=" * 60
    )

    tests = [
        test_build,
        test_relative_interval,
        test_extract_stable_centers,
        test_extract_transitions,
        test_stable_relationships,
        test_tonic_transition_evidence,
        test_candidate_generation,
        test_components_present,
        test_score_range,
        test_margin,
        test_evidence_only,
        test_protection,
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

    print(
        "=" * 60
    )

    print(
        "STATUS: PASS"
    )


if __name__ == "__main__":
    run()