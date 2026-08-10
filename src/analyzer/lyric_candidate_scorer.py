"""
PhoenixVoiceEngine - Lyric Candidate Scorer V1.0

Phase 2 after LyricCandidateGenerator V1.1.

This module DOES NOT correct lyrics. It scores candidate evidence and returns
a recommendation level:
    HIGH_CONFIDENCE
    MEDIUM_CONFIDENCE
    LOW_CONFIDENCE
    KEEP_ORIGINAL

Evidence used:
- Whisper candidate confidence
- improvement over original ASR confidence
- local lyric context
- repeated wording / structural support inside the same song
- whether the candidate is the original token

No artist/song-specific dictionary is used.
"""

from __future__ import annotations

from dataclasses import dataclass, asdict
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any, Dict, List, Tuple
import json
import re


ARABIC_DIACRITICS = re.compile(
    r"[\u0610-\u061A\u064B-\u065F\u0670\u06D6-\u06ED]"
)


def normalize_token(text: str) -> str:
    text = str(text or "").strip()
    text = ARABIC_DIACRITICS.sub("", text)
    text = text.replace("ـ", "")
    text = text.replace("أ", "ا").replace("إ", "ا").replace("آ", "ا")
    text = text.replace("ى", "ي")
    return text


def tokens(text: str) -> List[str]:
    return [normalize_token(x) for x in str(text or "").split() if normalize_token(x)]


@dataclass
class Evidence:
    asr_confidence: float
    confidence_gain: float
    local_context: float
    repetition_support: float
    original_penalty: float
    total_score: float
    decision: str


class LyricCandidateScorer:
    """
    Score candidates without changing the lyric.

    The scorer is deliberately conservative:
    a candidate can receive HIGH_CONFIDENCE only when multiple evidence
    sources agree. A high Whisper confidence by itself is not enough.
    """

    VERSION = "1.0.0"

    def __init__(
        self,
        high_threshold: float = 78.0,
        medium_threshold: float = 60.0,
        min_confidence_gain: float = 5.0,
    ) -> None:
        self.high_threshold = float(high_threshold)
        self.medium_threshold = float(medium_threshold)
        self.min_confidence_gain = float(min_confidence_gain)

    @staticmethod
    def _all_words(report: Dict[str, Any]) -> List[Dict[str, Any]]:
        result: List[Dict[str, Any]] = []
        for segment in report.get("segments", []):
            result.extend(segment.get("words", []))
        result.sort(key=lambda x: float(x.get("start_time", 0.0) or 0.0))
        return result

    @staticmethod
    def _context_score(
        words: List[Dict[str, Any]],
        target_index: int,
        candidate: str,
        radius: int = 3,
    ) -> float:
        """
        Compare the candidate against repeated local contexts.

        We look for the same neighboring words around other occurrences.
        This is intentionally generic and song-independent.
        """
        if not words:
            return 0.0

        start = max(0, target_index - radius)
        end = min(len(words), target_index + radius + 1)

        left = [
            normalize_token(w.get("text", ""))
            for w in words[start:target_index]
        ]
        right = [
            normalize_token(w.get("text", ""))
            for w in words[target_index + 1:end]
        ]

        best = 0.0

        for i, word in enumerate(words):
            if i == target_index:
                continue

            other = normalize_token(word.get("text", ""))
            if not other:
                continue

            # Compare only occurrences whose word itself is a possible
            # contextual anchor. The candidate need not already occur.
            other_left = [
                normalize_token(w.get("text", ""))
                for w in words[max(0, i - radius):i]
            ]
            other_right = [
                normalize_token(w.get("text", ""))
                for w in words[i + 1:min(len(words), i + radius + 1)]
            ]

            left_similarity = SequenceMatcher(
                None, left, other_left
            ).ratio() if left and other_left else 0.0

            right_similarity = SequenceMatcher(
                None, right, other_right
            ).ratio() if right and other_right else 0.0

            context_similarity = (left_similarity + right_similarity) / 2.0

            # If the candidate itself occurs elsewhere with similar context,
            # this is strong repetition evidence.
            if other == normalize_token(candidate):
                best = max(best, context_similarity)

        return round(best * 100.0, 2)

    @staticmethod
    def _repetition_support(
        words: List[Dict[str, Any]],
        target_index: int,
        candidate: str,
        radius: int = 5,
    ) -> float:
        candidate_key = normalize_token(candidate)
        if not candidate_key:
            return 0.0

        target_left = [
            normalize_token(w.get("text", ""))
            for w in words[max(0, target_index - radius):target_index]
        ]
        target_right = [
            normalize_token(w.get("text", ""))
            for w in words[target_index + 1:min(len(words), target_index + radius + 1)]
        ]

        occurrences = []
        for i, word in enumerate(words):
            if i == target_index:
                continue
            if normalize_token(word.get("text", "")) != candidate_key:
                continue

            left = [
                normalize_token(w.get("text", ""))
                for w in words[max(0, i - radius):i]
            ]
            right = [
                normalize_token(w.get("text", ""))
                for w in words[i + 1:min(len(words), i + radius + 1)]
            ]

            left_score = SequenceMatcher(None, target_left, left).ratio()
            right_score = SequenceMatcher(None, target_right, right).ratio()
            occurrences.append((left_score + right_score) / 2.0)

        if not occurrences:
            return 0.0

        # Repetition evidence is stronger when the candidate appears in a
        # matching context, but does not dominate acoustic evidence.
        return round(min(100.0, max(occurrences) * 100.0), 2)

    def _score_candidate(
        self,
        words: List[Dict[str, Any]],
        target_index: int,
        original: str,
        original_confidence: float,
        candidate: Dict[str, Any],
    ) -> Tuple[float, Evidence]:
        text = str(candidate.get("text", "")).strip()
        confidence = float(candidate.get("confidence", 0.0) or 0.0)

        original_key = normalize_token(original)
        candidate_key = normalize_token(text)

        confidence_gain = max(0.0, confidence - original_confidence)

        # Acoustic evidence: 45% of total.
        acoustic = max(0.0, min(100.0, confidence))

        # Improvement over original: up to 20 points.
        gain_score = min(100.0, confidence_gain * 4.0)

        # Context/repetition are deliberately capped.
        context = self._context_score(words, target_index, text)
        repetition = self._repetition_support(words, target_index, text)

        original_penalty = 0.0
        if candidate_key == original_key:
            original_penalty = 8.0

        total = (
            acoustic * 0.45
            + gain_score * 0.20
            + context * 0.15
            + repetition * 0.20
            - original_penalty
        )

        total = max(0.0, min(100.0, total))

        if candidate_key == original_key:
            decision = "KEEP_ORIGINAL"
        elif (
            total >= self.high_threshold
            and confidence_gain >= self.min_confidence_gain
            and repetition >= 45.0
        ):
            decision = "HIGH_CONFIDENCE"
        elif total >= self.medium_threshold:
            decision = "MEDIUM_CONFIDENCE"
        else:
            decision = "LOW_CONFIDENCE"

        evidence = Evidence(
            asr_confidence=round(acoustic, 2),
            confidence_gain=round(confidence_gain, 2),
            local_context=round(context, 2),
            repetition_support=round(repetition, 2),
            original_penalty=round(original_penalty, 2),
            total_score=round(total, 2),
            decision=decision,
        )

        return total, evidence

    def score_report(
        self,
        candidate_report: Dict[str, Any],
        lyric_report: Dict[str, Any],
    ) -> Dict[str, Any]:
        words = self._all_words(lyric_report)
        scored_reports: List[Dict[str, Any]] = []

        for report in candidate_report.get("reports", []):
            word_index = int(report.get("word_index", 1))
            target_index = max(0, min(len(words) - 1, word_index - 1))

            scored_candidates = []

            for candidate in report.get("candidates", []):
                score, evidence = self._score_candidate(
                    words=words,
                    target_index=target_index,
                    original=str(report.get("original_text", "")),
                    original_confidence=float(
                        report.get("original_confidence", 0.0) or 0.0
                    ),
                    candidate=candidate,
                )

                item = dict(candidate)
                item["evidence"] = asdict(evidence)
                scored_candidates.append(item)

            scored_candidates.sort(
                key=lambda x: float(
                    x["evidence"].get("total_score", 0.0)
                ),
                reverse=True,
            )

            # Never select a replacement automatically in this phase.
            recommendation = "KEEP_ORIGINAL"
            if scored_candidates:
                non_original = [
                    x for x in scored_candidates
                    if x["evidence"]["decision"] != "KEEP_ORIGINAL"
                ]
                if non_original:
                    recommendation = non_original[0]["evidence"]["decision"]

            scored_reports.append(
                {
                    "word_index": word_index,
                    "original_text": report.get("original_text", ""),
                    "original_confidence": report.get(
                        "original_confidence", 0.0
                    ),
                    "start_time": report.get("start_time", 0.0),
                    "end_time": report.get("end_time", 0.0),
                    "recommendation": recommendation,
                    "candidates": scored_candidates,
                }
            )

        return {
            "engine": "LyricCandidateScorer",
            "version": self.VERSION,
            "policy": "evidence_only_no_auto_correction",
            "high_threshold": self.high_threshold,
            "medium_threshold": self.medium_threshold,
            "min_confidence_gain": self.min_confidence_gain,
            "reports": scored_reports,
        }

    def score_file(
        self,
        candidate_json: str,
        lyric_json: str,
        output_json: str,
    ) -> Dict[str, Any]:
        with open(candidate_json, "r", encoding="utf-8") as handle:
            candidate_report = json.load(handle)

        with open(lyric_json, "r", encoding="utf-8") as handle:
            lyric_report = json.load(handle)

        result = self.score_report(candidate_report, lyric_report)

        with open(output_json, "w", encoding="utf-8") as handle:
            json.dump(result, handle, ensure_ascii=False, indent=2)

        return result