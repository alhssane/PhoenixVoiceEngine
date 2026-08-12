"""
PhoenixVoiceEngine
Tonic Relative Microtonal Evidence V1.0

Analyzes stable pitch centers relative to candidate tonic pitch classes.

IMPORTANT:
- Evidence only.
- No tonic decision.
- No maqam decision.
- No jins decision.
- No source pitch modification.
- No timing modification.
- No performance modification.

The analyzer compares the measured microtonal centers of observed
pitch classes against their expected 12-TET relationships to each
candidate tonic.

This is intentionally different from a global microtonal ratio.

Example:

    candidate tonic = G

    G  -> relative 0 cents
    G# -> relative 100 cents
    A# -> relative 300 cents
    C  -> relative 500 cents
    D  -> relative 700 cents

The measured stable centers are then evaluated against those
relative expectations.
"""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any, Dict, List, Optional


class TonicRelativeMicrotonalEvidence:
    VERSION = "1.0.0"
    FEATURE_VERSION = "1.0.0"
    PATCH_VERSION = "1.0.0"

    NOTE_NAMES = (
        "C",
        "C#",
        "D",
        "D#",
        "E",
        "F",
        "F#",
        "G",
        "G#",
        "A",
        "A#",
        "B",
    )

    # ---------------------------------------------------------------
    # IO
    # ---------------------------------------------------------------

    @staticmethod
    def _load(path: str) -> Dict[str, Any]:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    @staticmethod
    def _save(
        path: str,
        data: Dict[str, Any],
    ) -> None:

        output = Path(path)

        output.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        with open(
            output,
            "w",
            encoding="utf-8",
        ) as f:

            json.dump(
                data,
                f,
                ensure_ascii=False,
                indent=2,
            )

    # ---------------------------------------------------------------
    # NOTE HELPERS
    # ---------------------------------------------------------------

    @classmethod
    def _name(
        cls,
        pitch_class: int,
    ) -> str:

        return cls.NOTE_NAMES[
            int(pitch_class) % 12
        ]

    @staticmethod
    def _clamp(
        value: float,
        minimum: float = 0.0,
        maximum: float = 1.0,
    ) -> float:

        return max(
            minimum,
            min(
                maximum,
                float(value),
            ),
        )

    # ---------------------------------------------------------------
    # CIRCULAR CENT DEVIATION
    # ---------------------------------------------------------------

    @staticmethod
    def _circular_cents(
        value: float,
    ) -> float:
        """
        Normalize cents to [-50, +50).

        This handles octave boundaries correctly.

        Examples:

            49  -> 49
            51  -> -49
            99  -> -1
            -51 -> 49
        """

        value = float(value)

        while value >= 50.0:
            value -= 100.0

        while value < -50.0:
            value += 100.0

        return value

    # ---------------------------------------------------------------
    # EXPECTED RELATIVE DISTANCE
    # ---------------------------------------------------------------

    @staticmethod
    def _relative_12tet(
        tonic_pitch_class: int,
        pitch_class: int,
    ) -> int:
        """
        Return the 12-TET relative interval in semitones.
        """

        return (
            int(pitch_class)
            - int(tonic_pitch_class)
        ) % 12

    @classmethod
    def _expected_cents(
        cls,
        tonic_pitch_class: int,
        pitch_class: int,
    ) -> float:
        """
        Expected 12-TET cents relative to candidate tonic.
        """

        relative = cls._relative_12tet(
            tonic_pitch_class,
            pitch_class,
        )

        return float(
            relative * 100
        )

    # ---------------------------------------------------------------
    # EXTRACT STABLE CENTERS
    # ---------------------------------------------------------------

    def _extract_stable_centers(
        self,
        data: Dict[str, Any],
    ) -> List[Dict[str, Any]]:

        evidence = data.get(
            "evidence",
            {},
        )

        centers = evidence.get(
            "stable_pitch_centers",
            [],
        )

        if not isinstance(
            centers,
            list,
        ):
            return []

        result = []

        for center in centers:

            if not isinstance(
                center,
                dict,
            ):
                continue

            pitch_class = center.get(
                "pitch_class"
            )

            measured_cents = center.get(
                "center_cents"
            )

            if pitch_class is None:
                continue

            if measured_cents is None:
                continue

            try:
                pitch_class = (
                    int(pitch_class) % 12
                )

                measured_cents = float(
                    measured_cents
                )

            except (
                TypeError,
                ValueError,
            ):
                continue

            result.append(
                {
                    "pitch_class": pitch_class,
                    "pitch_class_name": self._name(
                        pitch_class
                    ),
                    "center_cents": measured_cents,
                    "region_count": int(
                        center.get(
                            "region_count",
                            0,
                        )
                    ),
                    "total_duration": float(
                        center.get(
                            "total_duration",
                            0.0,
                        )
                    ),
                    "sample_count": int(
                        center.get(
                            "sample_count",
                            0,
                        )
                    ),
                    "raw_hz_sample_count": int(
                        center.get(
                            "raw_hz_sample_count",
                            0,
                        )
                    ),
                    "mean_stability_score": float(
                        center.get(
                            "mean_stability_score",
                            0.0,
                        )
                    ),
                }
            )

        return result

    # ---------------------------------------------------------------
    # CENTER RELATIVE OFFSET
    # ---------------------------------------------------------------

    def _relative_center(
        self,
        tonic_pitch_class: int,
        center: Dict[str, Any],
    ) -> Dict[str, Any]:

        pitch_class = int(
            center["pitch_class"]
        ) % 12

        expected_cents = (
            self._expected_cents(
                tonic_pitch_class,
                pitch_class,
            )
        )

        measured_cents = float(
            center["center_cents"]
        )

        # center_cents represents deviation from the
        # pitch-class's 12-TET reference.
        #
        # Therefore the observed relative position
        # is:
        #
        # expected interval + measured deviation.
        observed_relative_cents = (
            expected_cents
            + measured_cents
        )

        # Compare observed relative position against
        # the expected 12-TET relative position.
        #
        # The measured center itself is therefore the
        # primary microtonal deviation.
        deviation = self._circular_cents(
            measured_cents
        )

        absolute_deviation = abs(
            deviation
        )

        # Convert deviation into a bounded agreement score.
        #
        # 0 cents  -> 1.0
        # 25 cents -> 0.5
        # 50 cents -> 0.0
        agreement = self._clamp(
            1.0
            - (
                absolute_deviation
                / 50.0
            )
        )

        return {
            "pitch_class": pitch_class,
            "pitch_class_name": self._name(
                pitch_class
            ),
            "relative_12tet": (
                self._relative_12tet(
                    tonic_pitch_class,
                    pitch_class,
                )
            ),
            "expected_relative_cents": (
                expected_cents
            ),
            "measured_center_cents": (
                measured_cents
            ),
            "observed_relative_cents": (
                observed_relative_cents
            ),
            "deviation_cents": (
                round(
                    deviation,
                    4,
                )
            ),
            "absolute_deviation_cents": (
                round(
                    absolute_deviation,
                    4,
                )
            ),
            "microtonal_agreement": (
                round(
                    agreement,
                    6,
                )
            ),
            "region_count": center[
                "region_count"
            ],
            "total_duration": center[
                "total_duration"
            ],
            "sample_count": center[
                "sample_count"
            ],
            "mean_stability_score": center[
                "mean_stability_score"
            ],
        }

    # ---------------------------------------------------------------
    # CANDIDATE ANALYSIS
    # ---------------------------------------------------------------

    def _analyze_candidate(
        self,
        tonic_pitch_class: int,
        centers: List[Dict[str, Any]],
    ) -> Dict[str, Any]:

        tonic_pitch_class = (
            int(tonic_pitch_class) % 12
        )

        relative_centers = []

        for center in centers:

            relative_centers.append(
                self._relative_center(
                    tonic_pitch_class,
                    center,
                )
            )

        # -----------------------------------------------------------
        # Weighted agreement
        #
        # Long and stable centers should contribute more evidence
        # than extremely short unstable regions.
        # -----------------------------------------------------------

        weighted_sum = 0.0
        total_weight = 0.0

        for item in relative_centers:

            duration_weight = min(
                1.0,
                float(
                    item["total_duration"]
                ) / 10.0,
            )

            stability_weight = self._clamp(
                item[
                    "mean_stability_score"
                ]
            )

            region_weight = min(
                1.0,
                float(
                    item["region_count"]
                ) / 20.0,
            )

            weight = (
                0.50 * duration_weight
                + 0.30 * stability_weight
                + 0.20 * region_weight
            )

            weight = max(
                weight,
                0.05,
            )

            weighted_sum += (
                item[
                    "microtonal_agreement"
                ]
                * weight
            )

            total_weight += weight

        if total_weight > 0.0:

            weighted_agreement = (
                weighted_sum
                / total_weight
            )

        else:

            weighted_agreement = 0.0

        # -----------------------------------------------------------
        # Tonic-specific evidence
        # -----------------------------------------------------------

        tonic_center = None

        for item in relative_centers:

            if (
                item["pitch_class"]
                == tonic_pitch_class
            ):
                tonic_center = item
                break

        tonic_agreement = (
            tonic_center[
                "microtonal_agreement"
            ]
            if tonic_center
            else 0.0
        )

        # -----------------------------------------------------------
        # Coverage
        # -----------------------------------------------------------

        coverage = (
            min(
                1.0,
                len(relative_centers)
                / 12.0,
            )
        )

        # -----------------------------------------------------------
        # Evidence score
        #
        # We intentionally keep this descriptive.
        # It is not a tonic confidence.
        # -----------------------------------------------------------

        score = (
            0.75 * weighted_agreement
            + 0.15 * tonic_agreement
            + 0.10 * coverage
        )

        score = self._clamp(
            score
        )

        return {
            "tonic_pitch_class": (
                tonic_pitch_class
            ),

            "tonic_name": self._name(
                tonic_pitch_class
            ),

            "score": round(
                score,
                6,
            ),

            "weighted_microtonal_agreement": (
                round(
                    weighted_agreement,
                    6,
                )
            ),

            "tonic_center_agreement": (
                round(
                    tonic_agreement,
                    6,
                )
            ),

            "center_coverage": round(
                coverage,
                6,
            ),

            "stable_center_count": len(
                relative_centers
            ),

            "relative_centers": (
                relative_centers
            ),

            "evidence_only": True,
        }

    # ---------------------------------------------------------------
    # MAIN ANALYSIS
    # ---------------------------------------------------------------

    def analyze(
        self,
        stable_data: Dict[str, Any],
        candidates: Optional[
            List[int]
        ] = None,
    ) -> Dict[str, Any]:

        candidates = [
            int(x) % 12
            for x in (
                candidates
                or [7, 0]
            )
        ]

        centers = (
            self._extract_stable_centers(
                stable_data
            )
        )

        ranking = []

        for tonic in candidates:

            ranking.append(
                self._analyze_candidate(
                    tonic,
                    centers,
                )
            )

        ranking.sort(
            key=lambda x: x["score"],
            reverse=True,
        )

        top = (
            ranking[0]
            if ranking
            else None
        )

        second = (
            ranking[1]
            if len(ranking) > 1
            else None
        )

        margin = (
            round(
                top["score"]
                - second["score"],
                6,
            )
            if top and second
            else 0.0
        )

        return {
            "version": self.VERSION,

            "feature_version": (
                self.FEATURE_VERSION
            ),

            "patch_version": (
                self.PATCH_VERSION
            ),

            "input": {
                "stable_center_count": len(
                    centers
                ),

                "candidate_pitch_classes": (
                    candidates
                ),
            },

            "evidence": {
                "stable_centers": centers,
                "candidate_relative_evidence": (
                    ranking
                ),
            },

            "ranking": {
                "candidates": ranking,
                "top": top,
                "second": second,
                "margin": margin,
            },

            "decision": {
                "status": "EVIDENCE_ONLY",
                "tonic_pitch_class": None,
                "tonic_name": None,
                "maqam": None,
                "jins": None,
                "confidence": None,
                "reason": [
                    "TONIC_RELATIVE_MICROTONAL_EVIDENCE_ONLY"
                ],
            },

            "protection": {
                "source_pitch_modified": False,
                "source_timing_modified": False,
                "source_performance_modified": False,
                "tonic_decision_made": False,
                "maqam_decision_made": False,
                "jins_decision_made": False,
            },
        }

    # ---------------------------------------------------------------
    # FILE ANALYSIS
    # ---------------------------------------------------------------

    def analyze_file(
        self,
        stable_path: str,
        output_path: str,
        candidates: Optional[
            List[int]
        ] = None,
    ) -> Dict[str, Any]:

        stable_data = self._load(
            stable_path
        )

        result = self.analyze(
            stable_data,
            candidates=candidates,
        )

        self._save(
            output_path,
            result,
        )

        return result


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description=(
            "PhoenixVoiceEngine "
            "Tonic Relative Microtonal Evidence"
        )
    )

    parser.add_argument(
        "stable_path",
    )

    parser.add_argument(
        "output_path",
    )

    parser.add_argument(
        "--candidates",
        nargs="+",
        type=int,
        default=[7, 0],
    )

    args = parser.parse_args()

    analyzer = (
        TonicRelativeMicrotonalEvidence()
    )

    result = analyzer.analyze_file(
        stable_path=args.stable_path,
        output_path=args.output_path,
        candidates=args.candidates,
    )

    print(
        json.dumps(
            result,
            ensure_ascii=False,
            indent=2,
        )
    )