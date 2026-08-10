"""PhoenixVoiceEngine - conservative Arabic lyric correction."""

from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import asdict, dataclass
from difflib import SequenceMatcher
from typing import Any, Dict, Iterable, List, Optional
import json
import re

ARABIC_DIACRITICS = re.compile(r"[\u0610-\u061A\u064B-\u065F\u0670\u06D6-\u06ED]")


def normalize_token(text: str) -> str:
    text = str(text or "").strip()
    text = ARABIC_DIACRITICS.sub("", text)
    text = text.replace("ـ", "")
    text = text.replace("أ", "ا").replace("إ", "ا").replace("آ", "ا")
    text = text.replace("ى", "ي")
    return text


def similarity(a: str, b: str) -> float:
    return SequenceMatcher(None, normalize_token(a), normalize_token(b)).ratio()


@dataclass
class Correction:
    index: int
    original: str
    corrected: str
    confidence: float
    correction_confidence: float
    reason: str

    @property
    def changed(self) -> bool:
        return self.original != self.corrected


class LyricCorrectionEngine:
    """Conservative correction based only on repeated evidence in the ASR report.

    It never contains song-specific lyrics and never changes timings.
    """

    def __init__(
        self,
        min_source_confidence: float = 88.0,
        strong_confidence: float = 95.0,
        min_similarity: float = 0.78,
        min_occurrences: int = 2,
    ) -> None:
        self.min_source_confidence = float(min_source_confidence)
        self.strong_confidence = float(strong_confidence)
        self.min_similarity = float(min_similarity)
        self.min_occurrences = int(min_occurrences)

    @staticmethod
    def _iter_words(report: Dict[str, Any]) -> Iterable[Dict[str, Any]]:
        for segment in report.get("segments", []):
            yield from segment.get("words", [])

    def _build_evidence(self, words: List[Dict[str, Any]]) -> Dict[str, Counter]:
        evidence: Dict[str, Counter] = defaultdict(Counter)
        for word in words:
            text = str(word.get("text", "")).strip()
            confidence = float(word.get("confidence", 0.0) or 0.0)
            if text and confidence >= self.min_source_confidence:
                evidence[normalize_token(text)][text] += 1
        return evidence

    def _best_variant(
        self,
        original: str,
        evidence: Dict[str, Counter],
    ) -> Optional[tuple[str, float, str]]:
        key = normalize_token(original)
        if not key:
            return None

        # Prefer repeated spellings with the same normalized Arabic form.
        if key in evidence and sum(evidence[key].values()) >= self.min_occurrences:
            variant, count = evidence[key].most_common(1)[0]
            if variant != original:
                return variant, min(99.0, 75.0 + count * 5.0), "repeated normalized spelling"

        candidates = []
        for variants in evidence.values():
            total = sum(variants.values())
            if total < self.min_occurrences:
                continue
            variant, count = variants.most_common(1)[0]
            score = similarity(original, variant)
            if variant != original and score >= self.min_similarity:
                candidates.append((score, count, variant))

        if not candidates:
            return None

        candidates.sort(key=lambda item: (item[0], item[1]), reverse=True)
        score, count, variant = candidates[0]
        confidence = min(99.0, 60.0 + (score - self.min_similarity) * 100.0 + min(20.0, count * 4.0))
        return variant, confidence, f"repeated similar token (similarity={score:.2f}, support={count})"

    def correct_report(self, report: Dict[str, Any]) -> Dict[str, Any]:
        result = json.loads(json.dumps(report, ensure_ascii=False))
        words = list(self._iter_words(result))
        evidence = self._build_evidence(words)
        corrections: List[Correction] = []

        for position, word in enumerate(words, start=1):
            original = str(word.get("text", "")).strip()
            confidence = float(word.get("confidence", 0.0) or 0.0)

            if confidence >= self.strong_confidence:
                corrections.append(Correction(
                    position, original, original, confidence, 100.0,
                    "high-confidence ASR token preserved",
                ))
                continue

            candidate = self._best_variant(original, evidence)
            if candidate is None:
                corrections.append(Correction(
                    position, original, original, confidence, confidence,
                    "no sufficiently strong internal evidence",
                ))
                continue

            corrected, correction_confidence, reason = candidate
            word["original_text"] = original
            word["text"] = corrected
            word["correction_applied"] = corrected != original
            word["correction_confidence"] = round(correction_confidence, 2)
            word["correction_reason"] = reason

            corrections.append(Correction(
                position, original, corrected, confidence,
                correction_confidence, reason,
            ))

        for segment in result.get("segments", []):
            segment["corrected_text"] = " ".join(
                str(w.get("text", "")).strip()
                for w in segment.get("words", [])
                if str(w.get("text", "")).strip()
            )

        result["corrected_text"] = " ".join(
            str(w.get("text", "")).strip() for w in words
            if str(w.get("text", "")).strip()
        )
        result["correction"] = {
            "engine": "LyricCorrectionEngine",
            "version": "1.0.0",
            "mode": "conservative_internal_evidence",
            "changed_word_count": sum(c.changed for c in corrections),
            "total_word_count": len(corrections),
            "corrections": [asdict(c) for c in corrections if c.changed],
        }
        return result

    def correct_file(self, input_path: str, output_path: str) -> Dict[str, Any]:
        with open(input_path, "r", encoding="utf-8") as handle:
            report = json.load(handle)
        corrected = self.correct_report(report)
        with open(output_path, "w", encoding="utf-8") as handle:
            json.dump(corrected, handle, ensure_ascii=False, indent=2)
        return corrected