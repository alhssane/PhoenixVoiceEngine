"""
PhoenixVoiceEngine
Jins Discriminator V1.0
"""

from src.maqam.jins_discriminator import JinsDiscriminator


def stable_fixture():
    return {
        "evidence": {
            "tonic_relative_stable_centers": [
                {
                    "relative_12tet": 0,
                    "total_duration": 10.0,
                    "mean_stability_score": 0.8,
                    "median_region_deviation_cents": 5.0,
                },
                {
                    "relative_12tet": 1,
                    "total_duration": 8.0,
                    "mean_stability_score": 0.8,
                    "median_region_deviation_cents": 7.0,
                },
                {
                    "relative_12tet": 3,
                    "total_duration": 6.0,
                    "mean_stability_score": 0.7,
                    "median_region_deviation_cents": 8.0,
                },
                {
                    "relative_12tet": 5,
                    "total_duration": 5.0,
                    "mean_stability_score": 0.7,
                    "median_region_deviation_cents": 9.0,
                },
            ]
        }
    }


def cadence_fixture():
    return {
        "evidence": {
            "cadences": {
                "final_pitch_class_counts": {
                    "7": 12,
                    "0": 4,
                }
            }
        }
    }


def test_build():
    assert JinsDiscriminator.PATCH_VERSION == "1.0.0"


def test_candidate_generation():
    r = JinsDiscriminator().analyze(
        stable_fixture(),
        cadence_fixture(),
        tonic_pitch_class=7,
    )
    assert len(r["ranking"]["candidates"]) == 8


def test_score_range():
    r = JinsDiscriminator().analyze(
        stable_fixture(),
        cadence_fixture(),
        tonic_pitch_class=7,
    )
    for x in r["ranking"]["candidates"]:
        assert 0.0 <= x["score"] <= 1.0


def test_bayati_kurd_coarse_evidence_can_tie():
    r = JinsDiscriminator().analyze(
        stable_fixture(),
        cadence_fixture(),
        tonic_pitch_class=7,
        candidates=["BAYATI", "KURD"],
    )
    assert r["ranking"]["candidates"][0]["score"] == \
        r["ranking"]["candidates"][1]["score"]


def test_evidence_only():
    r = JinsDiscriminator().analyze(
        stable_fixture(),
        cadence_fixture(),
        tonic_pitch_class=7,
    )
    assert r["decision"]["status"] == "EVIDENCE_ONLY"
    assert r["decision"]["maqam"] is None
    assert r["decision"]["jins"] is None


def test_protection():
    r = JinsDiscriminator().analyze(
        stable_fixture(),
        cadence_fixture(),
        tonic_pitch_class=7,
    )
    assert r["protection"]["source_pitch_modified"] is False
    assert r["protection"]["source_timing_modified"] is False
    assert r["protection"]["maqam_decision_made"] is False


def run():
    print("PhoenixVoiceEngine")
    print("Jins Discriminator V1.0")
    print("=" * 60)

    tests = [
        test_build,
        test_candidate_generation,
        test_score_range,
        test_bayati_kurd_coarse_evidence_can_tie,
        test_evidence_only,
        test_protection,
    ]

    for i, fn in enumerate(tests, 1):
        fn()
        print(f"TEST {i}: {fn.__name__} - PASS")

    print("=" * 60)
    print("STATUS: PASS")


if __name__ == "__main__":
    run()
