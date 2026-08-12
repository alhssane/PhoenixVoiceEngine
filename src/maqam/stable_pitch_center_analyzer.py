"""
PhoenixVoiceEngine
Stable Pitch Center Analyzer V1.0.2

Temporal stable-region analysis for raw pitch evidence.

Design:
- Evidence only.
- No pitch/timing correction.
- No maqam/jins decision.
- Uses temporal continuity instead of requiring a large global
  percentage of all samples for a pitch class.
- Fast pitch motion is treated as movement, not a stable center.
- Small oscillations can remain part of a stable region.
"""

from __future__ import annotations

import json
import math
from collections import defaultdict
from pathlib import Path
from statistics import median
from typing import Any, Dict, Iterable, List, Optional, Tuple


PITCH_KEYS = (
    "pitch_hz", "frequency_hz", "freq_hz", "raw_pitch_hz",
    "f0_hz", "frequency", "pitch", "hz",
)
MIDI_KEYS = ("midi_note", "midi", "midi_mean")
TIME_KEYS = ("start_time", "time", "timestamp")


class StablePitchCenterAnalyzer:
    VERSION = "1.0.0"
    FEATURE_VERSION = "1.0.0"
    PATCH_VERSION = "1.0.2"

    def __init__(
        self,
        min_samples: int = 8,
        max_spread_cents: float = 35.0,
        min_stability_ratio: float = 0.20,
        min_region_duration: float = 0.20,
        max_step_cents: float = 28.0,
        center_bin_cents: float = 5.0,
    ) -> None:
        if min_samples < 1:
            raise ValueError("min_samples must be positive.")
        if max_spread_cents <= 0:
            raise ValueError("max_spread_cents must be positive.")
        if not 0 < min_stability_ratio <= 1:
            raise ValueError("min_stability_ratio must be in (0, 1].")
        if min_region_duration <= 0:
            raise ValueError("min_region_duration must be positive.")
        if max_step_cents <= 0:
            raise ValueError("max_step_cents must be positive.")
        if center_bin_cents <= 0:
            raise ValueError("center_bin_cents must be positive.")

        self.min_samples = int(min_samples)
        self.max_spread_cents = float(max_spread_cents)
        self.min_stability_ratio = float(min_stability_ratio)
        self.min_region_duration = float(min_region_duration)
        self.max_step_cents = float(max_step_cents)
        self.center_bin_cents = float(center_bin_cents)

    @staticmethod
    def _walk(value: Any) -> Iterable[Dict[str, Any]]:
        if isinstance(value, dict):
            yield value
            for child in value.values():
                yield from StablePitchCenterAnalyzer._walk(child)
        elif isinstance(value, list):
            for child in value:
                yield from StablePitchCenterAnalyzer._walk(child)

    @staticmethod
    def _numeric(d: Dict[str, Any], keys: Tuple[str, ...]) -> Optional[float]:
        for key in keys:
            value = d.get(key)
            if isinstance(value, (int, float)) and math.isfinite(float(value)):
                return float(value)
        return None

    @staticmethod
    def _hz_to_midi(hz: float) -> Optional[float]:
        if hz <= 0:
            return None
        return 69.0 + 12.0 * math.log2(hz / 440.0)

    @staticmethod
    def _pc_name(pc: int) -> str:
        return (
            "C", "C#", "D", "D#", "E", "F",
            "F#", "G", "G#", "A", "A#", "B"
        )[pc % 12]

    @staticmethod
    def _cents(midi: float) -> float:
        return (midi - round(midi)) * 100.0

    @staticmethod
    def _circular_cents_delta(a: float, b: float) -> float:
        # Values are already centered around nearest MIDI (-50,+50).
        delta = a - b
        while delta > 50:
            delta -= 100
        while delta < -50:
            delta += 100
        return delta

    def _extract(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        samples = []

        for order, d in enumerate(self._walk(data)):
            hz = self._numeric(d, PITCH_KEYS)
            midi = None
            source = None

            if hz is not None and hz > 0:
                midi = self._hz_to_midi(hz)
                source = "RAW_HZ"
            else:
                midi = self._numeric(d, MIDI_KEYS)
                if midi is not None:
                    source = "MIDI"

            if midi is None:
                continue

            time = self._numeric(d, TIME_KEYS)
            samples.append({
                "order": order,
                "midi": float(midi),
                "pitch_class": int(round(midi)) % 12,
                "cents": self._cents(float(midi)),
                "time": time,
                "source": source,
            })

        # Temporal analysis must have time. If time is absent, retain order
        # but do not pretend that order is a duration.
        timed = [x for x in samples if x["time"] is not None]
        if len(timed) >= 2:
            samples = sorted(
                samples,
                key=lambda x: (
                    x["time"] is None,
                    x["time"] if x["time"] is not None else x["order"],
                ),
            )
        return samples

    def _stable_regions(self, samples: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        timed = [
            s for s in samples
            if s["time"] is not None
        ]

        if len(timed) < self.min_samples:
            return []

        regions = []
        current = [timed[0]]

        for sample in timed[1:]:
            previous = current[-1]
            time_gap = float(sample["time"]) - float(previous["time"])
            pitch_delta = abs(
                self._circular_cents_delta(
                    float(sample["cents"]),
                    float(previous["cents"]),
                )
            )

            # A large time gap or large pitch movement starts a new region.
            if (
                time_gap < 0
                or time_gap > 0.50
                or pitch_delta > self.max_step_cents
            ):
                regions.append(current)
                current = [sample]
            else:
                current.append(sample)

        regions.append(current)

        output = []

        for region in regions:
            if len(region) < self.min_samples:
                continue

            start = float(region[0]["time"])
            end = float(region[-1]["time"])
            duration = max(0.0, end - start)

            if duration < self.min_region_duration:
                continue

            values = [float(x["cents"]) for x in region]
            center = median(values)
            deviations = [
                abs(self._circular_cents_delta(v, center))
                for v in values
            ]
            mad = median(deviations) if deviations else 0.0

            if mad > self.max_spread_cents:
                continue

            # Dominant pitch class is determined from the actual region,
            # not corrected.
            counts = defaultdict(int)
            for x in region:
                counts[int(x["pitch_class"])] += 1
            dominant_pc = max(counts, key=counts.get)
            dominant_ratio = counts[dominant_pc] / len(region)

            if dominant_ratio < self.min_stability_ratio:
                continue

            raw_count = sum(
                1 for x in region if x["source"] == "RAW_HZ"
            )

            output.append({
                "start_time": round(start, 6),
                "end_time": round(end, 6),
                "duration": round(duration, 6),
                "pitch_class": dominant_pc,
                "pitch_class_name": self._pc_name(dominant_pc),
                "center_cents": round(center, 4),
                "sample_count": len(region),
                "raw_hz_sample_count": raw_count,
                "dominant_pitch_class_ratio": round(
                    dominant_ratio, 6
                ),
                "median_absolute_deviation_cents": round(
                    mad, 4
                ),
                "stability_score": round(
                    min(
                        1.0,
                        0.5 * dominant_ratio
                        + 0.5 * max(
                            0.0,
                            1.0 - mad / self.max_spread_cents,
                        ),
                    ),
                    6,
                ),
            })

        return output

    def _merge_centers(
        self,
        regions: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        grouped: Dict[int, List[Dict[str, Any]]] = defaultdict(list)
        for region in regions:
            grouped[region["pitch_class"]].append(region)

        centers = []

        for pc, items in grouped.items():
            # Weight each region by duration, preserving each region's
            # measured center rather than changing source samples.
            total_weight = sum(max(x["duration"], 1e-9) for x in items)
            weighted_center = sum(
                x["center_cents"] * max(x["duration"], 1e-9)
                for x in items
            ) / total_weight

            deviations = [
                abs(
                    self._circular_cents_delta(
                        x["center_cents"],
                        weighted_center,
                    )
                )
                for x in items
            ]

            centers.append({
                "pitch_class": pc,
                "pitch_class_name": self._pc_name(pc),
                "region_count": len(items),
                "total_duration": round(
                    sum(x["duration"] for x in items), 6
                ),
                "sample_count": sum(
                    x["sample_count"] for x in items
                ),
                "raw_hz_sample_count": sum(
                    x["raw_hz_sample_count"] for x in items
                ),
                "center_cents": round(
                    weighted_center, 4
                ),
                "median_region_deviation_cents": round(
                    median(deviations) if deviations else 0.0,
                    4,
                ),
                "mean_stability_score": round(
                    sum(x["stability_score"] for x in items)
                    / len(items),
                    6,
                ),
            })

        centers.sort(
            key=lambda x: x["total_duration"],
            reverse=True,
        )
        return centers

    def analyze(
        self,
        data: Dict[str, Any],
        tonic_pitch_class: Optional[int] = None,
    ) -> Dict[str, Any]:
        samples = self._extract(data)
        regions = self._stable_regions(samples)
        centers = self._merge_centers(regions)

        tonic_relative = []
        if tonic_pitch_class is not None:
            tonic = int(tonic_pitch_class) % 12
            for center in centers:
                relative = (
                    center["pitch_class"] - tonic
                ) % 12
                if relative == 12:
                    relative = 0
                tonic_relative.append({
                    **center,
                    "relative_12tet": relative,
                })

        timed_count = sum(
            1 for s in samples if s["time"] is not None
        )

        return {
            "version": self.VERSION,
            "feature_version": self.FEATURE_VERSION,
            "patch_version": self.PATCH_VERSION,
            "input": {
                "sample_count": len(samples),
                "timed_sample_count": timed_count,
                "raw_hz_sample_count": sum(
                    1 for s in samples
                    if s["source"] == "RAW_HZ"
                ),
                "midi_sample_count": sum(
                    1 for s in samples
                    if s["source"] == "MIDI"
                ),
                "tonic_pitch_class": (
                    None if tonic_pitch_class is None
                    else int(tonic_pitch_class) % 12
                ),
            },
            "evidence": {
                "stable_regions": regions,
                "stable_pitch_centers": centers,
                "tonic_relative_stable_centers": tonic_relative,
            },
            "analysis": {
                "method": "TEMPORAL_STABLE_REGION_ANALYSIS",
                "raw_pitch_preserved": True,
                "timing_preserved": True,
                "no_auto_correction": True,
                "no_maqam_decision": True,
                "movement_is_not_stable_center": True,
                "parameters": {
                    "min_samples": self.min_samples,
                    "max_spread_cents": self.max_spread_cents,
                    "min_stability_ratio": self.min_stability_ratio,
                    "min_region_duration": self.min_region_duration,
                    "max_step_cents": self.max_step_cents,
                    "center_bin_cents": self.center_bin_cents,
                },
            },
            "decision": {
                "status": "EVIDENCE_ONLY",
                "maqam": None,
                "jins": None,
                "confidence": None,
            },
        }

    def analyze_file(
        self,
        input_path: str,
        output_path: str,
        tonic_pitch_class: Optional[int] = None,
    ) -> Dict[str, Any]:
        with open(input_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        result = self.analyze(
            data,
            tonic_pitch_class=tonic_pitch_class,
        )

        output = Path(output_path)
        output.parent.mkdir(parents=True, exist_ok=True)
        with open(output, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)

        return result
