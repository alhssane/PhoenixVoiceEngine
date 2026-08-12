"""
PhoenixVoiceEngine
Raw Pitch Jins Evidence Analyzer V1.0

Purpose:
    Build evidence around a candidate tonic using the highest-resolution pitch
    values available in the supplied performance/profile JSON.

Important:
    This module is evidence-only.
    It never corrects pitch, timing, contour, or maqam.
    It never invents microtones.

The extractor accepts common raw-pitch representations and recursively
searches event dictionaries. If only MIDI is available, it explicitly reports
that microtonal evidence is unavailable rather than manufacturing it.
"""

from __future__ import annotations

import json
import math
from collections import Counter
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple


PITCH_KEYS = (
    "pitch_hz",
    "frequency_hz",
    "freq_hz",
    "raw_pitch_hz",
    "f0_hz",
    "frequency",
    "pitch",
    "hz",
)

MIDI_KEYS = (
    "midi_note",
    "midi",
    "midi_mean",
)

TIME_KEYS = (
    "start_time",
    "time",
    "timestamp",
)


class RawPitchJinsEvidenceAnalyzer:
    VERSION = "1.0.0"
    FEATURE_VERSION = "1.0.0"
    PATCH_VERSION = "1.0.0"

    def __init__(self, tonic_pitch_class: Optional[int] = None) -> None:
        self.tonic_pitch_class = (
            None if tonic_pitch_class is None
            else int(tonic_pitch_class) % 12
        )

    @staticmethod
    def _walk_dicts(value: Any) -> Iterable[Dict[str, Any]]:
        if isinstance(value, dict):
            yield value
            for child in value.values():
                yield from RawPitchJinsEvidenceAnalyzer._walk_dicts(child)
        elif isinstance(value, list):
            for child in value:
                yield from RawPitchJinsEvidenceAnalyzer._walk_dicts(child)

    @staticmethod
    def _first_numeric(d: Dict[str, Any], keys: Tuple[str, ...]) -> Optional[float]:
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
    def _cents_from_nearest_midi(midi: float) -> float:
        nearest = round(midi)
        return (midi - nearest) * 100.0

    @staticmethod
    def _pitch_class(midi: float) -> int:
        return int(round(midi)) % 12

    def _extract_samples(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        samples: List[Dict[str, Any]] = []

        for order, d in enumerate(self._walk_dicts(data)):
            hz = self._first_numeric(d, PITCH_KEYS)
            midi = self._first_numeric(d, MIDI_KEYS)

            source = None
            if hz is not None and hz > 0:
                converted = self._hz_to_midi(hz)
                if converted is not None:
                    midi = converted
                    source = "RAW_HZ"
            elif midi is not None:
                source = "MIDI"

            if midi is None:
                continue

            sample = {
                "order": order,
                "midi": round(float(midi), 6),
                "pitch_class": self._pitch_class(midi),
                "cents_from_nearest_midi": round(
                    self._cents_from_nearest_midi(midi), 4
                ),
                "source": source,
            }

            time = self._first_numeric(d, TIME_KEYS)
            if time is not None:
                sample["time"] = round(time, 6)

            samples.append(sample)

        return samples

    def _microtonal_evidence(self, samples: List[Dict[str, Any]]) -> Dict[str, Any]:
        raw = [s for s in samples if s["source"] == "RAW_HZ"]

        if not raw:
            return {
                "available": False,
                "sample_count": 0,
                "mean_absolute_cents": None,
                "median_absolute_cents": None,
                "nontrivial_cents_ratio": None,
                "reason": "NO_RAW_HZ_EVIDENCE",
            }

        cents = [abs(float(s["cents_from_nearest_midi"])) for s in raw]
        nontrivial = sum(1 for c in cents if c >= 5.0)

        ordered = sorted(cents)
        mid = len(ordered) // 2
        median = (
            ordered[mid]
            if len(ordered) % 2
            else (ordered[mid - 1] + ordered[mid]) / 2
        )

        return {
            "available": True,
            "sample_count": len(raw),
            "mean_absolute_cents": round(
                sum(cents) / len(cents), 4
            ),
            "median_absolute_cents": round(median, 4),
            "nontrivial_cents_ratio": round(
                nontrivial / len(cents), 6
            ),
            "reason": "RAW_HZ_PRESENT",
        }

    def _tonic_relative_bins(
        self,
        samples: List[Dict[str, Any]],
        tonic_pc: Optional[int],
    ) -> Dict[str, Any]:
        if tonic_pc is None:
            return {
                "available": False,
                "reason": "TONIC_NOT_SUPPLIED",
                "bins_25_cents": {},
            }

        bins: Counter[str] = Counter()

        for sample in samples:
            midi = float(sample["midi"])
            relative = (midi - tonic_pc) % 12.0
            # 25-cent bins retain more information than pitch class alone,
            # while avoiding any claim of maqam-specific microtonal intervals.
            bucket = round(relative * 4.0) / 4.0
            bins[f"{bucket:.2f}"] += 1

        total = sum(bins.values())

        return {
            "available": bool(total),
            "reason": "RAW_OR_MIDI_RELATIVE_BINS",
            "sample_count": total,
            "bins_25_cents": {
                k: round(v / total, 6)
                for k, v in bins.most_common()
            },
        }

    def analyze(
        self,
        data: Dict[str, Any],
        tonic_pitch_class: Optional[int] = None,
    ) -> Dict[str, Any]:
        tonic = (
            self.tonic_pitch_class
            if tonic_pitch_class is None
            else int(tonic_pitch_class) % 12
        )

        samples = self._extract_samples(data)
        raw_count = sum(
            1 for s in samples if s["source"] == "RAW_HZ"
        )
        midi_count = sum(
            1 for s in samples if s["source"] == "MIDI"
        )

        return {
            "version": self.VERSION,
            "feature_version": self.FEATURE_VERSION,
            "patch_version": self.PATCH_VERSION,
            "input": {
                "sample_count": len(samples),
                "raw_hz_sample_count": raw_count,
                "midi_sample_count": midi_count,
                "tonic_pitch_class": tonic,
            },
            "evidence": {
                "microtonal": self._microtonal_evidence(samples),
                "tonic_relative": self._tonic_relative_bins(
                    samples, tonic
                ),
                "pitch_class_counts": dict(
                    Counter(str(s["pitch_class"]) for s in samples)
                ),
            },
            "analysis": {
                "raw_pitch_preserved": True,
                "timing_preserved": True,
                "no_auto_correction": True,
                "no_maqam_decision": True,
                "microtonal_interpretation": (
                    "EVIDENCE_ONLY"
                ),
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

        result = self.analyze(data, tonic_pitch_class)

        output = Path(output_path)
        output.parent.mkdir(parents=True, exist_ok=True)
        with open(output, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)

        return result
