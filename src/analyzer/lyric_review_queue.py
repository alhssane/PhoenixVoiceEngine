"""
PhoenixVoiceEngine - Lyric Review Queue V1.0.1

Human-review queue for lyric candidates.

V1.0.1 changes:
- Calibrated review priority levels.
- HIGH requires strong margin + multiple evidence supports.
- MEDIUM requires clear margin + at least one support.
- LOW requires positive but weaker margin.
- Original lyric is never modified.
- No automatic correction is performed.

Policy:
- Detect.
- Rank.
- Present for human review.
- Never silently change the original lyric.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List
import json


class LyricReviewQueue:
    VERSION = "1.0.1"

    REVIEW_DECISIONS = {
        "REVIEW_CANDIDATE",
        "RECOMMEND_CORRECTION",
        "STRONG_CORRECTION",
    }

    def __init__(
        self,
        min_margin: float = 0.0,
        min_supports: int = 1,
        include_recommendations: bool = True,
        include_strong_corrections: bool = True,
    ) -> None:
        if min_margin < 0:
            raise ValueError(
                "min_margin must be >= 0."
            )

        if min_supports < 0:
            raise ValueError(
                "min_supports must be >= 0."
            )

        self.min_margin = float(min_margin)
        self.min_supports = int(min_supports)
        self.include_recommendations = bool(
            include_recommendations
        )
        self.include_strong_corrections = bool(
            include_strong_corrections
        )

    # =========================================================
    # Basic helpers
    # =========================================================

    @staticmethod
    def _float(
        value: Any,
        default: float = 0.0,
    ) -> float:
        try:
            return float(value)
        except (TypeError, ValueError):
            return default

    @staticmethod
    def _int(
        value: Any,
        default: int = 0,
    ) -> int:
        try:
            return int(value)
        except (TypeError, ValueError):
            return default

    @staticmethod
    def _normalize(
        text: Any,
    ) -> str:
        return str(text or "").strip().lower()

    @classmethod
    def _is_original(
        cls,
        candidate_text: str,
        original_text: str,
    ) -> bool:
        return (
            cls._normalize(candidate_text)
            == cls._normalize(original_text)
        )

    # =========================================================
    # Candidate eligibility
    # =========================================================

    def _is_reviewable_candidate(
        self,
        candidate: Dict[str, Any],
        original_text: str,
    ) -> bool:
        text = str(
            candidate.get("text", "")
        ).strip()

        if not text:
            return False

        # Never place the original token itself
        # in the review queue.
        if self._is_original(
            text,
            original_text,
        ):
            return False

        fusion = candidate.get(
            "fusion",
            {},
        )

        decision = str(
            fusion.get(
                "decision",
                "",
            )
        ).strip().upper()

        margin = self._float(
            fusion.get(
                "margin_vs_original",
            )
        )

        supports = self._int(
            fusion.get(
                "independent_support_count",
            )
        )

        # Candidate must have positive
        # comparative evidence.
        if margin <= self.min_margin:
            return False

        # Candidate must have the configured
        # minimum independent support.
        if supports < self.min_supports:
            return False

        if decision == "REVIEW_CANDIDATE":
            return True

        if (
            decision == "RECOMMEND_CORRECTION"
            and self.include_recommendations
        ):
            return True

        if (
            decision == "STRONG_CORRECTION"
            and self.include_strong_corrections
        ):
            return True

        return False

    # =========================================================
    # V1.0.1 Priority Calibration
    # =========================================================

    @staticmethod
    def _priority(
        candidate: Dict[str, Any],
        original_confidence: float,
    ) -> str:
        """
        V1.0.1 Priority Calibration.

        HIGH:
            margin >= 15
            AND independent supports >= 2

        MEDIUM:
            margin >= 10
            AND independent supports >= 1

        LOW:
            margin >= 5
            AND independent supports >= 1

        The priority does NOT mean that the
        candidate is correct.

        It only controls review order.
        """

        fusion = candidate.get(
            "fusion",
            {},
        )

        margin = float(
            fusion.get(
                "margin_vs_original",
                0.0,
            )
        )

        supports = int(
            fusion.get(
                "independent_support_count",
                0,
            )
        )

        # -----------------------------------------------------
        # HIGH
        # -----------------------------------------------------
        #
        # Strong comparative advantage with
        # multiple independent evidence families.
        #
        if (
            margin >= 15.0
            and supports >= 2
        ):
            return "HIGH"

        # -----------------------------------------------------
        # MEDIUM
        # -----------------------------------------------------
        #
        # Clear comparative advantage with
        # at least one independent evidence family.
        #
        if (
            margin >= 10.0
            and supports >= 1
        ):
            return "MEDIUM"

        # -----------------------------------------------------
        # LOW
        # -----------------------------------------------------
        #
        # Positive but weaker comparative advantage.
        #
        if (
            margin >= 5.0
            and supports >= 1
        ):
            return "LOW"

        # -----------------------------------------------------
        # Conservative fallback
        # -----------------------------------------------------
        #
        # _is_reviewable_candidate() normally prevents
        # candidates from reaching this branch unless
        # they have a positive margin.
        #
        return "LOW"

    @staticmethod
    def _priority_weight(
        priority: str,
    ) -> int:
        return {
            "HIGH": 3,
            "MEDIUM": 2,
            "LOW": 1,
        }.get(
            priority,
            0,
        )

    # =========================================================
    # Review item
    # =========================================================

    def _build_review_item(
        self,
        report: Dict[str, Any],
        candidate: Dict[str, Any],
    ) -> Dict[str, Any]:

        original_text = str(
            report.get(
                "original_text",
                "",
            )
        )

        original_confidence = self._float(
            report.get(
                "original_confidence",
            )
        )

        fusion = candidate.get(
            "fusion",
            {},
        )

        evidence = candidate.get(
            "evidence",
            {},
        )

        margin = self._float(
            fusion.get(
                "margin_vs_original",
            )
        )

        supports = self._int(
            fusion.get(
                "independent_support_count",
            )
        )

        priority = self._priority(
            candidate,
            original_confidence,
        )

        start_time = self._float(
            report.get(
                "start_time",
            )
        )

        end_time = self._float(
            report.get(
                "end_time",
            )
        )

        duration = max(
            0.0,
            end_time - start_time,
        )

        return {
            "review_id": (
                f"word_"
                f"{self._int(report.get('word_index')):04d}"
                f"_"
                f"{str(candidate.get('text', '')).strip()}"
            ),

            "word_index": self._int(
                report.get(
                    "word_index",
                )
            ),

            "original_text": original_text,

            "candidate_text": str(
                candidate.get(
                    "text",
                    "",
                )
            ).strip(),

            "original_confidence": (
                original_confidence
            ),

            "candidate_confidence": self._float(
                evidence.get(
                    "asr_confidence",
                )
            ),

            "start_time": start_time,

            "end_time": end_time,

            "duration": round(
                duration,
                3,
            ),

            "priority": priority,

            "decision": str(
                fusion.get(
                    "decision",
                    "",
                )
            ),

            "candidate_total_score": (
                self._float(
                    fusion.get(
                        "candidate_total_score",
                    )
                )
            ),

            "original_total_score": (
                self._float(
                    fusion.get(
                        "original_total_score",
                    )
                )
            ),

            "margin_vs_original": margin,

            "relative_margin": self._float(
                fusion.get(
                    "relative_margin",
                )
            ),

            "independent_support_count": (
                supports
            ),

            "evidence": {
                "candidate_score": self._float(
                    fusion.get(
                        "candidate_score",
                    )
                ),

                "candidate_acoustic_score": (
                    self._float(
                        fusion.get(
                            "candidate_acoustic_score",
                        )
                    )
                ),

                "confidence_gain": self._float(
                    fusion.get(
                        "confidence_gain",
                    )
                ),

                "context_score": self._float(
                    fusion.get(
                        "context_score",
                    )
                ),

                "repeated_context_score": (
                    self._float(
                        fusion.get(
                            "repeated_context_score",
                        )
                    )
                ),

                "phrase_support_score": (
                    self._float(
                        fusion.get(
                            "phrase_support_score",
                        )
                    )
                ),

                "position_score": self._float(
                    fusion.get(
                        "position_score",
                    )
                ),
            },

            "reasons": list(
                fusion.get(
                    "reasons",
                    [],
                )
            ),

            # Human review has not happened yet.
            "status": "PENDING_REVIEW",
        }

    # =========================================================
    # Main analysis
    # =========================================================

    def analyze(
        self,
        fusion_report: Dict[str, Any],
    ) -> Dict[str, Any]:

        queue: List[
            Dict[str, Any]
        ] = []

        reports = fusion_report.get(
            "reports",
            [],
        )

        for report in reports:

            original_text = str(
                report.get(
                    "original_text",
                    "",
                )
            )

            candidates = report.get(
                "candidates",
                [],
            )

            for candidate in candidates:

                if not self._is_reviewable_candidate(
                    candidate,
                    original_text,
                ):
                    continue

                queue.append(
                    self._build_review_item(
                        report,
                        candidate,
                    )
                )

        # =====================================================
        # Sort Review Queue
        # =====================================================
        #
        # 1. HIGH before MEDIUM before LOW
        # 2. Larger margin first
        # 3. More independent evidence first
        # 4. Earlier word first
        #
        queue.sort(
            key=lambda item: (
                -self._priority_weight(
                    item["priority"]
                ),
                -item[
                    "margin_vs_original"
                ],
                -item[
                    "independent_support_count"
                ],
                item[
                    "word_index"
                ],
            )
        )

        # =====================================================
        # Stable queue positions
        # =====================================================

        for position, item in enumerate(
            queue,
            start=1,
        ):
            item[
                "queue_position"
            ] = position

        # =====================================================
        # Statistics
        # =====================================================

        high = sum(
            1
            for item in queue
            if item["priority"] == "HIGH"
        )

        medium = sum(
            1
            for item in queue
            if item["priority"] == "MEDIUM"
        )

        low = sum(
            1
            for item in queue
            if item["priority"] == "LOW"
        )

        review_candidates = sum(
            1
            for item in queue
            if item["decision"]
            == "REVIEW_CANDIDATE"
        )

        recommendations = sum(
            1
            for item in queue
            if item["decision"]
            == "RECOMMEND_CORRECTION"
        )

        strong = sum(
            1
            for item in queue
            if item["decision"]
            == "STRONG_CORRECTION"
        )

        # =====================================================
        # Final result
        # =====================================================

        return {
            "engine": (
                "LyricReviewQueue"
            ),

            "version": self.VERSION,

            "source_engine": (
                fusion_report.get(
                    "engine",
                    "LyricEvidenceFusion",
                )
            ),

            "source_version": (
                fusion_report.get(
                    "version",
                    "unknown",
                )
            ),

            "mode": (
                "human_review_queue"
            ),

            "policy": (
                "human_review_only_no_auto_correction"
            ),

            "priority_calibration": {
                "HIGH": (
                    "margin >= 15.0 "
                    "and supports >= 2"
                ),
                "MEDIUM": (
                    "margin >= 10.0 "
                    "and supports >= 1"
                ),
                "LOW": (
                    "margin >= 5.0 "
                    "and supports >= 1"
                ),
            },

            "min_margin": (
                self.min_margin
            ),

            "min_independent_supports": (
                self.min_supports
            ),

            "include_recommendations": (
                self.include_recommendations
            ),

            "include_strong_corrections": (
                self.include_strong_corrections
            ),

            "source_report_count": len(
                reports
            ),

            "queue_count": len(
                queue
            ),

            "priority_counts": {
                "HIGH": high,
                "MEDIUM": medium,
                "LOW": low,
            },

            "decision_counts": {
                "REVIEW_CANDIDATE": (
                    review_candidates
                ),
                "RECOMMEND_CORRECTION": (
                    recommendations
                ),
                "STRONG_CORRECTION": (
                    strong
                ),
            },

            "queue": queue,
        }

    # =========================================================
    # File interface
    # =========================================================

    def analyze_file(
        self,
        fusion_json: str,
        output_json: str,
    ) -> Dict[str, Any]:

        with open(
            fusion_json,
            "r",
            encoding="utf-8",
        ) as f:

            fusion_report = json.load(f)

        result = self.analyze(
            fusion_report
        )

        path = Path(
            output_json
        )

        path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        path.write_text(
            json.dumps(
                result,
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )

        return result