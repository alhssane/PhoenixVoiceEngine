"""
PhoenixVoiceEngine - Lyric Context Analyzer V1.0

Analyzes contextual evidence for ASR lyric candidates without making a
correction decision.

Inputs:
    - original lyric extraction JSON
    - candidate generator JSON
    - optional phrase-match JSON

Evidence:
    1. Target position/alignment
    2. Immediate-neighbor consistency
    3. Repeated-context support
    4. Phrase-window support
    5. Candidate-vs-original contextual contrast

Important:
    This module NEVER selects a final lyric correction.
    It only adds context evidence to each candidate.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence
import json
import re


ARABIC_DIACRITICS = re.compile(
    r"[\u0610-\u061A\u064B-\u065F\u0670\u06D6-\u06ED]"
)

PUNCTUATION = ".,،؛:!?؟()[]{}\"'«»"


def normalize_token(text: str) -> str:
    text = str(text or "").strip()
    text = ARABIC_DIACRITICS.sub("", text)
    text = text.replace("ـ", "")
    text = text.replace("أ", "ا").replace("إ", "ا").replace("آ", "ا")
    text = text.replace("ى", "ي")
    return text.strip(PUNCTUATION).lower()


def tokenize(text: str) -> List[str]:
    return [
        normalize_token(token)
        for token in str(text or "").split()
        if normalize_token(token)
    ]


@dataclass
class ContextEvidence:
    position_score: float
    previous_neighbor_score: float
    next_neighbor_score: float
    repeated_context_score: float
    phrase_support_score: float
    contrast_score: float
    total_score: float
    decision: str
    reasons: List[str]

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ContextCandidate:
    text: str
    context: ContextEvidence

    def to_dict(self) -> Dict[str, Any]:
        return {
            "text": self.text,
            "context": self.context.to_dict(),
        }


class LyricContextAnalyzer:
    """
    Context-only evidence layer.

    The analyzer is intentionally conservative:
      - it does not edit lyric text;
      - it does not choose a correction;
      - it does not treat ASR confidence as contextual evidence;
      - it returns explicit evidence components for later fusion.
    """

    VERSION = "1.0.0"

    def __init__(
        self,
        context_radius: int = 2,
        strong_threshold: float = 75.0,
        supporting_threshold: float = 50.0,
    ) -> None:
        if context_radius < 1:
            raise ValueError("context_radius must be >= 1.")
        if not 0 <= supporting_threshold <= 100:
            raise ValueError("supporting_threshold must be 0..100.")
        if not 0 <= strong_threshold <= 100:
            raise ValueError("strong_threshold must be 0..100.")
        if strong_threshold < supporting_threshold:
            raise ValueError(
                "strong_threshold must be >= supporting_threshold."
            )

        self.context_radius = int(context_radius)
        self.strong_threshold = float(strong_threshold)
        self.supporting_threshold = float(supporting_threshold)

    # ------------------------------------------------------------------
    # Input helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _extract_words(lyrics_report: Dict[str, Any]) -> List[Dict[str, Any]]:
        words: List[Dict[str, Any]] = []

        if isinstance(lyrics_report.get("words"), list):
            words = list(lyrics_report["words"])
        else:
            for segment in lyrics_report.get("segments", []):
                words.extend(segment.get("words", []))

        words.sort(
            key=lambda word: (
                float(word.get("start_time", 0.0) or 0.0),
                int(word.get("index", 0) or 0),
            )
        )
        return words

    @staticmethod
    def _safe_float(value: Any, default: float = 0.0) -> float:
        try:
            return float(value)
        except (TypeError, ValueError):
            return default

    @staticmethod
    def _candidate_text(candidate: Dict[str, Any]) -> str:
        return str(candidate.get("text", "")).strip()

    # ------------------------------------------------------------------
    # Context
    # ------------------------------------------------------------------

    def _neighbor_tokens(
        self,
        words: Sequence[Dict[str, Any]],
        target_index: int,
    ) -> tuple[List[str], List[str]]:
        previous: List[str] = []
        following: List[str] = []

        for distance in range(1, self.context_radius + 1):
            p = target_index - distance
            if p >= 0:
                token = normalize_token(words[p].get("text", ""))
                if token:
                    previous.append(token)

            n = target_index + distance
            if n < len(words):
                token = normalize_token(words[n].get("text", ""))
                if token:
                    following.append(token)

        return previous, following

    def _position_score(
        self,
        report: Dict[str, Any],
        target_word: Dict[str, Any],
    ) -> float:
        target_start = self._safe_float(
            report.get("start_time", target_word.get("start_time", 0.0))
        )
        target_end = self._safe_float(
            report.get("end_time", target_word.get("end_time", target_start))
        )

        candidate_start = self._safe_float(
            report.get("_candidate_start", target_start)
        )
        candidate_end = self._safe_float(
            report.get("_candidate_end", target_end)
        )

        target_duration = max(0.001, target_end - target_start)
        candidate_duration = max(0.001, candidate_end - candidate_start)

        overlap = max(
            0.0,
            min(target_end, candidate_end)
            - max(target_start, candidate_start),
        )
        union = max(target_end, candidate_end) - min(
            target_start, candidate_start
        )
        iou = overlap / union if union > 0 else 0.0

        center_distance = abs(
            ((candidate_start + candidate_end) / 2.0)
            - ((target_start + target_end) / 2.0)
        )
        duration_ratio = min(
            target_duration, candidate_duration
        ) / max(target_duration, candidate_duration)

        center_score = max(
            0.0,
            1.0 - center_distance / max(target_duration, 0.25),
        )

        return round(
            max(
                0.0,
                min(
                    100.0,
                    (iou * 0.55 + center_score * 0.30 + duration_ratio * 0.15)
                    * 100.0,
                ),
            ),
            2,
        )

    @staticmethod
    def _neighbor_match(candidate: str, expected: Sequence[str]) -> float:
        # This method is intentionally simple. Candidate text itself is not
        # compared to neighboring words; the value is used only when a
        # repeated context occurrence confirms the candidate.
        return 100.0 if candidate in expected else 0.0

    def _find_repeated_context_support(
        self,
        words: Sequence[Dict[str, Any]],
        target_index: int,
        candidate: str,
    ) -> tuple[float, float, float, List[str]]:
        """
        Search the entire lyric for another occurrence where the same
        neighboring tokens surround the candidate.

        Returns:
            previous support, next support, combined support, reasons
        """
        candidate_norm = normalize_token(candidate)
        if not candidate_norm:
            return 0.0, 0.0, 0.0, []

        prev_context, next_context = self._neighbor_tokens(
            words, target_index
        )

        previous_hits = 0
        next_hits = 0
        full_hits = 0

        for index, word in enumerate(words):
            if index == target_index:
                continue

            if normalize_token(word.get("text", "")) != candidate_norm:
                continue

            other_prev, other_next = self._neighbor_tokens(words, index)

            # Compare only the context that is actually available around
            # the repeated occurrence. This correctly handles occurrences
            # near the beginning/end of the lyric.
            prev_available = min(len(prev_context), len(other_prev))
            next_available = min(len(next_context), len(other_next))

            prev_ok = (
                prev_available > 0
                and other_prev[:prev_available]
                == prev_context[:prev_available]
            )

            next_ok = (
                next_available > 0
                and other_next[:next_available]
                == next_context[:next_available]
            )

            if prev_ok:
                previous_hits += 1
            if next_ok:
                next_hits += 1

            prev_full = (
                len(prev_context) == 0
                or (
                    prev_available == len(prev_context)
                    and prev_ok
                )
            )

            # At the end of a lyric there may be fewer following words than
            # around the target. Matching every available following word is
            # sufficient evidence for the next side.
            next_full = (
                len(next_context) == 0
                or next_ok
            )

            if prev_full and next_full:
                full_hits += 1

        reasons: List[str] = []

        prev_score = 100.0 if previous_hits else 0.0
        next_score = 100.0 if next_hits else 0.0

        if full_hits:
            combined = 100.0
            reasons.append(
                f"exact repeated context found ({full_hits} occurrence(s))"
            )
        elif previous_hits or next_hits:
            combined = 60.0
            if previous_hits:
                reasons.append(
                    f"previous-neighbor context repeated ({previous_hits})"
                )
            if next_hits:
                reasons.append(
                    f"next-neighbor context repeated ({next_hits})"
                )
        else:
            combined = 0.0

        return prev_score, next_score, combined, reasons

    def _phrase_support(
        self,
        candidate: str,
        phrase_matches: Optional[Dict[str, Any]],
    ) -> float:
        if not phrase_matches:
            return 0.0

        candidate_norm = normalize_token(candidate)
        if not candidate_norm:
            return 0.0

        matches = phrase_matches.get("matches", [])
        support = 0.0

        for match in matches:
            first = tokenize(match.get("first_text", ""))
            second = tokenize(match.get("second_text", ""))

            if candidate_norm in first or candidate_norm in second:
                similarity = self._safe_float(
                    match.get("similarity", 0.0)
                )
                support = max(support, similarity * 100.0)

        return round(min(100.0, support), 2)

    # ------------------------------------------------------------------
    # Evidence
    # ------------------------------------------------------------------

    def _score_candidate(
        self,
        words: Sequence[Dict[str, Any]],
        target_index: int,
        candidate: Dict[str, Any],
        phrase_matches: Optional[Dict[str, Any]],
        target_start: float,
        target_end: float,
    ) -> ContextEvidence:
        text = self._candidate_text(candidate)
        candidate_start = self._safe_float(
            candidate.get("start_time", target_start)
        )
        candidate_end = self._safe_float(
            candidate.get("end_time", target_end)
        )

        position_report = {
            "start_time": target_start,
            "end_time": target_end,
            "_candidate_start": candidate_start,
            "_candidate_end": candidate_end,
        }

        position_score = self._position_score(
            position_report,
            {
                "start_time": target_start,
                "end_time": target_end,
            },
        )

        prev_score, next_score, repeated_score, reasons = (
            self._find_repeated_context_support(
                words,
                target_index,
                text,
            )
        )

        phrase_score = self._phrase_support(text, phrase_matches)

        original = normalize_token(words[target_index].get("text", ""))
        candidate_norm = normalize_token(text)

        # Contrast is deliberately bounded. It rewards a candidate only when
        # it has contextual evidence while the original has none. It does not
        # declare the candidate correct.
        if candidate_norm == original:
            contrast_score = 50.0
        elif repeated_score > 0 or phrase_score >= 70.0:
            contrast_score = 100.0
        else:
            contrast_score = 0.0

        # Context-only weighting. No ASR confidence is included here.
        total = (
            position_score * 0.20
            + prev_score * 0.15
            + next_score * 0.15
            + repeated_score * 0.30
            + phrase_score * 0.10
            + contrast_score * 0.10
        )

        total = round(max(0.0, min(100.0, total)), 2)

        if total >= self.strong_threshold:
            decision = "STRONG_CONTEXT"
        elif total >= self.supporting_threshold:
            decision = "SUPPORTING_CONTEXT"
        elif total <= 20.0:
            decision = "NO_CONTEXT_SUPPORT"
        else:
            decision = "WEAK_CONTEXT"

        if position_score >= 90:
            reasons.append("candidate timing overlaps target strongly")
        elif position_score < 50:
            reasons.append("candidate timing has weak target overlap")

        if phrase_score >= 70:
            reasons.append("phrase-match support is strong")

        if candidate_norm == original:
            reasons.append("candidate is the original ASR token")

        return ContextEvidence(
            position_score=round(position_score, 2),
            previous_neighbor_score=round(prev_score, 2),
            next_neighbor_score=round(next_score, 2),
            repeated_context_score=round(repeated_score, 2),
            phrase_support_score=round(phrase_score, 2),
            contrast_score=round(contrast_score, 2),
            total_score=total,
            decision=decision,
            reasons=reasons,
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def analyze(
        self,
        lyrics_report: Dict[str, Any],
        candidate_report: Dict[str, Any],
        phrase_matches: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        words = self._extract_words(lyrics_report)

        if not words:
            raise ValueError("Lyrics report contains no words.")

        reports: List[Dict[str, Any]] = []

        for report in candidate_report.get("reports", []):
            raw_index = int(report.get("word_index", 0) or 0)
            target_index = raw_index - 1

            if target_index < 0 or target_index >= len(words):
                reports.append(
                    {
                        **report,
                        "context_candidates": [],
                        "context_error": "word_index_out_of_range",
                    }
                )
                continue

            target_word = words[target_index]
            target_start = self._safe_float(
                target_word.get(
                    "start_time",
                    report.get("start_time", 0.0),
                )
            )
            target_end = self._safe_float(
                target_word.get(
                    "end_time",
                    report.get("end_time", target_start),
                )
            )

            context_candidates = []

            for candidate in report.get("candidates", []):
                evidence = self._score_candidate(
                    words=words,
                    target_index=target_index,
                    candidate=candidate,
                    phrase_matches=phrase_matches,
                    target_start=target_start,
                    target_end=target_end,
                )

                context_candidates.append(
                    ContextCandidate(
                        text=self._candidate_text(candidate),
                        context=evidence,
                    ).to_dict()
                )

            reports.append(
                {
                    **report,
                    "context_candidates": context_candidates,
                }
            )

        return {
            "engine": "LyricContextAnalyzer",
            "version": self.VERSION,
            "context_radius": self.context_radius,
            "strong_threshold": self.strong_threshold,
            "supporting_threshold": self.supporting_threshold,
            "word_count": len(words),
            "report_count": len(reports),
            "reports": reports,
        }

    def analyze_file(
        self,
        lyrics_json: str,
        candidates_json: str,
        output_json: str,
        phrase_matches_json: Optional[str] = None,
    ) -> Dict[str, Any]:
        with open(lyrics_json, "r", encoding="utf-8") as handle:
            lyrics_report = json.load(handle)

        with open(candidates_json, "r", encoding="utf-8") as handle:
            candidate_report = json.load(handle)

        phrase_matches = None
        if phrase_matches_json:
            phrase_path = Path(phrase_matches_json)
            if phrase_path.exists():
                with phrase_path.open("r", encoding="utf-8") as handle:
                    phrase_matches = json.load(handle)

        result = self.analyze(
            lyrics_report=lyrics_report,
            candidate_report=candidate_report,
            phrase_matches=phrase_matches,
        )

        output_path = Path(output_json)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(
            json.dumps(result, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

        return result