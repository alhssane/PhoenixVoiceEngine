"""
PhoenixVoiceEngine - Lyric Evidence Fusion V1.1.1
Review Calibration.

V1.1.1 keeps the V1.1 comparative scoring model and changes only the
decision layer:

- A non-original candidate with a positive comparative margin but fewer
  than the required independent evidence families becomes REVIEW_CANDIDATE.
- A candidate that does not beat the original remains KEEP_ORIGINAL.
- Correction recommendations still require independent evidence.
- No lyric text is ever modified automatically.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict, List
import json
import re


ARABIC_DIACRITICS = re.compile(r"[\u0610-\u061A\u064B-\u065F\u0670\u06D6-\u06ED]")
PUNCTUATION = ".,،؛:!?؟()[]{}\"'«»"


def normalize_token(text: str) -> str:
    text = str(text or "").strip()
    text = ARABIC_DIACRITICS.sub("", text)
    text = text.replace("ـ", "")
    text = text.replace("أ", "ا").replace("إ", "ا").replace("آ", "ا")
    text = text.replace("ى", "ي")
    return text.strip(PUNCTUATION).lower()


@dataclass
class ComparativeEvidence:
    candidate_score: float
    candidate_acoustic_score: float
    confidence_gain: float
    context_score: float
    repeated_context_score: float
    phrase_support_score: float
    position_score: float
    independent_support_count: int
    candidate_total_score: float
    original_total_score: float
    margin_vs_original: float
    relative_margin: float
    decision: str
    reasons: List[str]

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class LyricEvidenceFusion:
    VERSION = "1.1.1"

    def __init__(
        self,
        strong_threshold: float = 82.0,
        recommend_threshold: float = 70.0,
        review_threshold: float = 50.0,
        min_margin: float = 10.0,
        strong_margin: float = 18.0,
        min_independent_supports: int = 2,
    ) -> None:
        if not 0 <= review_threshold <= recommend_threshold <= strong_threshold <= 100:
            raise ValueError("Thresholds must satisfy 0 <= review <= recommend <= strong <= 100.")
        if min_margin < 0 or strong_margin < min_margin:
            raise ValueError("Margins must satisfy 0 <= min_margin <= strong_margin.")
        if min_independent_supports < 1:
            raise ValueError("min_independent_supports must be >= 1.")

        self.strong_threshold = float(strong_threshold)
        self.recommend_threshold = float(recommend_threshold)
        self.review_threshold = float(review_threshold)
        self.min_margin = float(min_margin)
        self.strong_margin = float(strong_margin)
        self.min_independent_supports = int(min_independent_supports)

    @staticmethod
    def _float(value: Any, default: float = 0.0) -> float:
        try:
            return float(value)
        except (TypeError, ValueError):
            return default

    @staticmethod
    def _is_original(candidate_text: str, original_text: str) -> bool:
        return normalize_token(candidate_text) == normalize_token(original_text)

    @staticmethod
    def _context_map(items: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
        result: Dict[str, Dict[str, Any]] = {}
        for item in items:
            key = normalize_token(item.get("text", ""))
            if key:
                result[key] = item.get("context", {})
        return result

    def _support_families(
        self,
        candidate_score: float,
        confidence_gain: float,
        context_score: float,
        repeated_context: float,
        phrase_support: float,
        position_score: float,
    ) -> tuple[int, List[str]]:
        count = 0
        reasons: List[str] = []

        if candidate_score >= 70.0 or confidence_gain >= 8.0:
            count += 1
            reasons.append("candidate/acoustic evidence is strong")

        if context_score >= 70.0:
            count += 1
            reasons.append("context evidence is strong")

        if repeated_context >= 70.0 or phrase_support >= 70.0:
            count += 1
            reasons.append("repetition/phrase evidence is strong")

        if position_score >= 90.0:
            count += 1
            reasons.append("timing/position alignment is strong")

        return count, reasons

    def _score_original(self, candidate: Dict[str, Any], context: Dict[str, Any]) -> float:
        ev = candidate.get("evidence", {})
        return round(max(0.0, min(100.0, (
            self._float(ev.get("total_score")) * 0.20
            + self._float(ev.get("asr_confidence")) * 0.10
            + self._float(context.get("total_score")) * 0.30
            + max(
                self._float(ev.get("repetition_support")),
                self._float(context.get("repeated_context_score")),
            ) * 0.15
            + self._float(context.get("phrase_support_score")) * 0.10
            + self._float(context.get("position_score")) * 0.05
        ))), 2)

    def _fuse(
        self,
        candidate: Dict[str, Any],
        context: Dict[str, Any],
        original_text: str,
        original_total: float,
    ) -> ComparativeEvidence:
        ev = candidate.get("evidence", {})

        candidate_score = self._float(ev.get("total_score"))
        acoustic = self._float(ev.get("asr_confidence"))
        gain = self._float(ev.get("confidence_gain"))
        context_score = self._float(context.get("total_score"))
        repeated = self._float(context.get("repeated_context_score"))
        phrase = self._float(context.get("phrase_support_score"))
        position = self._float(context.get("position_score"))

        supports, reasons = self._support_families(
            candidate_score, gain, context_score, repeated, phrase, position
        )

        total = (
            candidate_score * 0.20
            + acoustic * 0.10
            + min(100.0, gain * 5.0) * 0.10
            + context_score * 0.30
            + repeated * 0.15
            + phrase * 0.10
            + position * 0.05
        )
        total = round(max(0.0, min(100.0, total)), 2)
        margin = round(total - original_total, 2)
        denominator = max(abs(original_total), 1.0)
        relative_margin = round((margin / denominator) * 100.0, 2)

        original = self._is_original(candidate.get("text", ""), original_text)

        if original:
            decision = "KEEP_ORIGINAL"
            reasons.append("candidate is the original ASR token")
        elif margin <= 0:
            decision = "KEEP_ORIGINAL"
            reasons.append("candidate does not beat the original")
        elif supports < self.min_independent_supports:
            # V1.1.1 calibration:
            # A positive margin is meaningful enough to surface for review,
            # but not enough to recommend a correction.
            decision = "REVIEW_CANDIDATE"
            reasons.append("candidate beats original but lacks enough independent evidence")
        elif margin < self.min_margin:
            decision = "REVIEW_CANDIDATE"
            reasons.append("candidate has multiple evidence families but margin is below recommendation threshold")
        elif total >= self.strong_threshold and margin >= self.strong_margin and supports >= 3:
            decision = "STRONG_CORRECTION"
            reasons.append("candidate clearly beats original with multiple independent evidence families")
        elif total >= self.recommend_threshold and margin >= self.min_margin:
            decision = "RECOMMEND_CORRECTION"
            reasons.append("candidate beats original with sufficient independent evidence")
        else:
            decision = "REVIEW_CANDIDATE"
            reasons.append("candidate has positive comparative evidence but is not decisive")

        return ComparativeEvidence(
            candidate_score=round(candidate_score, 2),
            candidate_acoustic_score=round(acoustic, 2),
            confidence_gain=round(gain, 2),
            context_score=round(context_score, 2),
            repeated_context_score=round(repeated, 2),
            phrase_support_score=round(phrase, 2),
            position_score=round(position, 2),
            independent_support_count=supports,
            candidate_total_score=total,
            original_total_score=round(original_total, 2),
            margin_vs_original=margin,
            relative_margin=relative_margin,
            decision=decision,
            reasons=reasons,
        )

    def analyze(self, scored_report: Dict[str, Any], context_report: Dict[str, Any]) -> Dict[str, Any]:
        context_reports = {
            int(r.get("word_index", 0) or 0): r
            for r in context_report.get("reports", [])
        }

        reports: List[Dict[str, Any]] = []

        for report in scored_report.get("reports", []):
            index = int(report.get("word_index", 0) or 0)
            original_text = str(report.get("original_text", ""))
            original_confidence = self._float(report.get("original_confidence"))

            ctx_report = context_reports.get(index, {})
            context_candidates = self._context_map(
                ctx_report.get("context_candidates", [])
            )

            candidates = report.get("candidates", [])
            original_candidate = next(
                (c for c in candidates if self._is_original(c.get("text", ""), original_text)),
                None,
            )

            original_context = context_candidates.get(normalize_token(original_text), {})
            if original_candidate is not None:
                original_total = self._score_original(original_candidate, original_context)
            else:
                original_total = round(
                    max(
                        0.0,
                        min(
                            100.0,
                            original_confidence * 0.10
                            + self._float(original_context.get("total_score")) * 0.40,
                        ),
                    ),
                    2,
                )

            fused = []
            for candidate in candidates:
                item = dict(candidate)
                text = str(candidate.get("text", "")).strip()
                evidence = self._fuse(
                    candidate,
                    context_candidates.get(normalize_token(text), {}),
                    original_text,
                    original_total,
                )
                item["fusion"] = evidence.to_dict()
                fused.append(item)

            fused.sort(
                key=lambda c: c["fusion"]["candidate_total_score"],
                reverse=True
            )

            non_original = [
                c for c in fused
                if not self._is_original(c.get("text", ""), original_text)
            ]

            recommendation = "KEEP_ORIGINAL"
            recommended_candidate = None

            # Find the best *eligible* non-original candidate, but preserve
            # REVIEW_CANDIDATE when it has a positive comparative margin.
            best_review = next(
                (
                    c for c in non_original
                    if c["fusion"]["decision"] == "REVIEW_CANDIDATE"
                    and c["fusion"]["margin_vs_original"] > 0
                ),
                None,
            )

            best_recommendation = next(
                (
                    c for c in non_original
                    if c["fusion"]["decision"]
                    in {"STRONG_CORRECTION", "RECOMMEND_CORRECTION"}
                ),
                None,
            )

            if best_recommendation is not None:
                recommendation = best_recommendation["fusion"]["decision"]
                recommended_candidate = best_recommendation["text"]
            elif best_review is not None:
                recommendation = "REVIEW_CANDIDATE"

            reports.append({
                "word_index": index,
                "original_text": original_text,
                "original_confidence": original_confidence,
                "start_time": report.get("start_time", 0.0),
                "end_time": report.get("end_time", 0.0),
                "original_fusion_score": original_total,
                "recommendation": recommendation,
                "recommended_candidate": recommended_candidate,
                "candidates": fused,
            })

        return {
            "engine": "LyricEvidenceFusion",
            "version": self.VERSION,
            "mode": "comparative_decision_engine",
            "calibration": "review_calibration",
            "policy": "evidence_only_no_auto_correction",
            "strong_threshold": self.strong_threshold,
            "recommend_threshold": self.recommend_threshold,
            "review_threshold": self.review_threshold,
            "min_margin": self.min_margin,
            "strong_margin": self.strong_margin,
            "min_independent_supports": self.min_independent_supports,
            "report_count": len(reports),
            "reports": reports,
        }

    def analyze_file(self, scored_candidates_json: str, context_json: str, output_json: str) -> Dict[str, Any]:
        with open(scored_candidates_json, "r", encoding="utf-8") as f:
            scored = json.load(f)
        with open(context_json, "r", encoding="utf-8") as f:
            context = json.load(f)

        result = self.analyze(scored, context)
        path = Path(output_json)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(result, ensure_ascii=False, indent=2),
            encoding="utf-8"
        )
        return result