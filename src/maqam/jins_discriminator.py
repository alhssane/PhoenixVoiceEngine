"""
PhoenixVoiceEngine
Jins Discriminator V1.0

Evidence-only comparison of candidate jins using:
- stable pitch centers
- tonic-relative scale degrees
- cadence/transition evidence

This module does NOT decide a maqam and never modifies source data.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional


class JinsDiscriminator:
    VERSION = "1.0.0"
    FEATURE_VERSION = "1.0.0"
    PATCH_VERSION = "1.0.0"

    # Coarse 12-TET interval profiles. They are evidence templates only.
    PROFILES = {
        "BAYATI": {
            "root_jins": "Bayati",
            "degrees": {0, 1, 3, 5},
        },
        "KURD": {
            "root_jins": "Kurd",
            "degrees": {0, 1, 3, 5},
        },
        "NAHAWAND": {
            "root_jins": "Nahawand",
            "degrees": {0, 2, 3, 5, 7},
        },
        "HIJAZ": {
            "root_jins": "Hijaz",
            "degrees": {0, 1, 4, 5},
        },
        "SABA": {
            "root_jins": "Saba",
            "degrees": {0, 1, 3, 4},
        },
        "RAST": {
            "root_jins": "Rast",
            "degrees": {0, 2, 4, 5},
        },
        "AJAM": {
            "root_jins": "Ajam",
            "degrees": {0, 2, 4, 5, 7},
        },
        "SIKAH": {
            "root_jins": "Sikah",
            "degrees": {0, 1, 3, 5},
        },
    }

    def _load(self, path: str) -> Dict[str, Any]:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    @staticmethod
    def _safe_float(value: Any, default: float = 0.0) -> float:
        try:
            return float(value)
        except (TypeError, ValueError):
            return default

    def _centers(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        return data.get("evidence", {}).get(
            "tonic_relative_stable_centers", []
        )

    def _center_map(self, data: Dict[str, Any]) -> Dict[int, Dict[str, Any]]:
        return {
            int(x["relative_12tet"]): x
            for x in self._centers(data)
            if "relative_12tet" in x
        }

    def _pitch_evidence_score(
        self,
        candidate: str,
        center_map: Dict[int, Dict[str, Any]],
    ) -> float:
        profile = self.PROFILES[candidate]
        expected = profile["degrees"]

        if not center_map:
            return 0.0

        supported = 0.0
        total = 0.0

        for degree, item in center_map.items():
            weight = max(
                self._safe_float(item.get("total_duration")),
                0.001,
            )
            stability = max(
                0.0,
                min(
                    1.0,
                    self._safe_float(
                        item.get("mean_stability_score"),
                        0.0,
                    ),
                ),
            )
            value = weight * (0.5 + 0.5 * stability)
            total += value

            if degree in expected:
                supported += value

        return supported / total if total else 0.0

    def _microtonal_profile_score(
        self,
        candidate: str,
        center_map: Dict[int, Dict[str, Any]],
    ) -> float:
        """
        V1 is deliberately conservative.

        The coarse profiles do not assert a specific Arabic maqam tuning.
        Microtonal cents are reported as evidence but do not create a
        maqam claim by themselves.
        """
        if not center_map:
            return 0.0

        relevant = [
            x for degree, x in center_map.items()
            if degree in self.PROFILES[candidate]["degrees"]
        ]
        if not relevant:
            return 0.0

        # Reward reproducible, low-deviation centers only.
        values = []
        for x in relevant:
            mad = abs(
                self._safe_float(
                    x.get("median_region_deviation_cents"),
                    100.0,
                )
            )
            values.append(max(0.0, min(1.0, 1.0 - mad / 50.0)))

        return sum(values) / len(values)

    def _transition_score(
        self,
        cadence: Dict[str, Any],
        tonic_pitch_class: Optional[int],
    ) -> float:
        if not cadence:
            return 0.0

        final_counts = cadence.get("cadences", {}).get(
            "final_pitch_class_counts", {}
        )
        if not final_counts or tonic_pitch_class is None:
            return 0.0

        tonic = str(int(tonic_pitch_class) % 12)
        total = sum(
            self._safe_float(v) for v in final_counts.values()
        )
        if total <= 0:
            return 0.0

        return self._safe_float(final_counts.get(tonic, 0)) / total

    def _candidate(self, name: str, centers: Dict[int, Dict[str, Any]],
                   cadence: Dict[str, Any],
                   tonic: Optional[int]) -> Dict[str, Any]:
        pitch = self._pitch_evidence_score(name, centers)
        micro = self._microtonal_profile_score(name, centers)
        cadence_score = self._transition_score(cadence, tonic)

        # V1 intentionally keeps cadence weak and does not invent
        # discrimination where Bayati/Kurd share the same coarse degrees.
        score = (
            0.60 * pitch
            + 0.25 * micro
            + 0.15 * cadence_score
        )

        return {
            "jins": self.PROFILES[name]["root_jins"],
            "candidate_maqam": name,
            "score": round(score, 6),
            "components": {
                "stable_pitch_evidence": round(pitch, 6),
                "microtonal_center_reproducibility": round(micro, 6),
                "tonic_cadence_evidence": round(
                    cadence_score, 6
                ),
            },
            "evidence_only": True,
        }

    def analyze(
        self,
        stable_centers: Dict[str, Any],
        cadence: Dict[str, Any],
        tonic_pitch_class: Optional[int] = None,
        candidates: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        names = candidates or list(self.PROFILES.keys())
        centers = self._center_map(stable_centers)

        ranked = [
            self._candidate(
                name,
                centers,
                cadence,
                tonic_pitch_class,
            )
            for name in names
            if name in self.PROFILES
        ]
        ranked.sort(
            key=lambda x: x["score"],
            reverse=True,
        )

        top = ranked[0] if ranked else None
        second = ranked[1] if len(ranked) > 1 else None
        margin = (
            top["score"] - second["score"]
            if top and second else 0.0
        )

        return {
            "version": self.VERSION,
            "feature_version": self.FEATURE_VERSION,
            "patch_version": self.PATCH_VERSION,
            "input": {
                "stable_center_count": len(centers),
                "tonic_pitch_class": tonic_pitch_class,
                "candidate_count": len(ranked),
            },
            "ranking": {
                "candidates": ranked,
                "top": top,
                "second": second,
                "margin": round(margin, 6),
            },
            "decision": {
                "status": "EVIDENCE_ONLY",
                "maqam": None,
                "jins": None,
                "confidence": None,
                "reason": ["JINS_EVIDENCE_ONLY"],
            },
            "protection": {
                "source_pitch_modified": False,
                "source_timing_modified": False,
                "source_performance_modified": False,
                "maqam_decision_made": False,
                "microtonal_claim_from_12tet": False,
            },
        }

    def analyze_files(
        self,
        stable_centers_path: str,
        cadence_path: str,
        output_path: str,
        tonic_pitch_class: Optional[int] = None,
        candidates: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        stable = self._load(stable_centers_path)
        cadence = self._load(cadence_path)

        result = self.analyze(
            stable,
            cadence,
            tonic_pitch_class=tonic_pitch_class,
            candidates=candidates,
        )

        output = Path(output_path)
        output.parent.mkdir(parents=True, exist_ok=True)

        with open(output, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)

        return result
