"""PhoenixVoiceEngine - repeated lyric phrase matcher.

Finds likely repeated phrases in an ASR lyric report without containing
song-specific lyrics. It is an evidence layer for LyricCorrectionEngine.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from difflib import SequenceMatcher
from typing import Any, Dict, List, Sequence, Tuple
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


def token_similarity(a: str, b: str) -> float:
    return SequenceMatcher(None, normalize_token(a), normalize_token(b)).ratio()


def sequence_similarity(a: Sequence[str], b: Sequence[str]) -> float:
    na = [normalize_token(x) for x in a]
    nb = [normalize_token(x) for x in b]
    return SequenceMatcher(None, na, nb).ratio()


@dataclass
class PhraseOccurrence:
    occurrence_id: int
    start_time: float
    end_time: float
    words: List[str]

    @property
    def text(self) -> str:
        return " ".join(self.words)


@dataclass
class PhraseMatch:
    match_id: int
    first_occurrence: int
    second_occurrence: int
    similarity: float
    first_start: float
    first_end: float
    second_start: float
    second_end: float
    first_text: str
    second_text: str
    differing_positions: List[Dict[str, Any]]


class LyricPhraseMatcher:
    """Detect repeated phrases from word-level ASR timestamps."""

    def __init__(
        self,
        min_phrase_words: int = 3,
        max_phrase_words: int = 12,
        min_similarity: float = 0.72,
        min_confidence: float = 0.0,
        max_gap_seconds: float = 2.0,
    ) -> None:
        self.min_phrase_words = int(min_phrase_words)
        self.max_phrase_words = int(max_phrase_words)
        self.min_similarity = float(min_similarity)
        self.min_confidence = float(min_confidence)
        self.max_gap_seconds = float(max_gap_seconds)

    @staticmethod
    def _all_words(report: Dict[str, Any]) -> List[Dict[str, Any]]:
        words: List[Dict[str, Any]] = []
        for segment in report.get("segments", []):
            words.extend(segment.get("words", []))
        words.sort(key=lambda w: float(w.get("start_time", 0.0) or 0.0))
        return words

    def _valid_words(self, report: Dict[str, Any]) -> List[Dict[str, Any]]:
        result = []
        for word in self._all_words(report):
            text = str(word.get("text", "")).strip()
            confidence = float(word.get("confidence", 0.0) or 0.0)
            if text and confidence >= self.min_confidence:
                result.append(word)
        return result

    def _make_windows(self, words: List[Dict[str, Any]]) -> List[PhraseOccurrence]:
        occurrences: List[PhraseOccurrence] = []
        next_id = 1

        for size in range(self.min_phrase_words, self.max_phrase_words + 1):
            for i in range(0, len(words) - size + 1):
                window = words[i:i + size]
                start = float(window[0].get("start_time", 0.0) or 0.0)
                end = float(window[-1].get("end_time", start) or start)

                # Reject windows containing unusually large internal gaps.
                valid = True
                for left, right in zip(window, window[1:]):
                    left_end = float(left.get("end_time", 0.0) or 0.0)
                    right_start = float(right.get("start_time", 0.0) or 0.0)
                    if right_start - left_end > self.max_gap_seconds:
                        valid = False
                        break

                if not valid:
                    continue

                occurrences.append(
                    PhraseOccurrence(
                        occurrence_id=next_id,
                        start_time=start,
                        end_time=end,
                        words=[str(w.get("text", "")).strip() for w in window],
                    )
                )
                next_id += 1

        return occurrences

    @staticmethod
    def _differences(
        first: Sequence[str],
        second: Sequence[str],
    ) -> List[Dict[str, Any]]:
        result: List[Dict[str, Any]] = []
        size = max(len(first), len(second))

        for i in range(size):
            a = first[i] if i < len(first) else None
            b = second[i] if i < len(second) else None

            if a is None or b is None:
                result.append({
                    "position": i,
                    "first": a,
                    "second": b,
                    "similarity": 0.0,
                })
                continue

            sim = token_similarity(a, b)
            if normalize_token(a) != normalize_token(b):
                result.append({
                    "position": i,
                    "first": a,
                    "second": b,
                    "similarity": round(sim, 4),
                })

        return result

    def find_matches(self, report: Dict[str, Any]) -> List[PhraseMatch]:
        words = self._valid_words(report)
        windows = self._make_windows(words)

        # Prefer the longest useful repeated phrases. We keep only one
        # representative match for a pair when a longer window covers it.
        candidates: List[PhraseMatch] = []
        match_id = 1

        for i in range(len(windows)):
            a = windows[i]

            for j in range(i + 1, len(windows)):
                b = windows[j]

                # Do not compare overlapping windows from nearly the same
                # location; they are not meaningful repetitions.
                if b.start_time <= a.end_time:
                    continue

                sim = sequence_similarity(a.words, b.words)
                if sim < self.min_similarity:
                    continue

                # A phrase with no lexical difference is useful as evidence
                # too, but we want different-token positions for correction.
                differences = self._differences(a.words, b.words)

                candidates.append(
                    PhraseMatch(
                        match_id=match_id,
                        first_occurrence=a.occurrence_id,
                        second_occurrence=b.occurrence_id,
                        similarity=round(sim, 4),
                        first_start=a.start_time,
                        first_end=a.end_time,
                        second_start=b.start_time,
                        second_end=b.end_time,
                        first_text=a.text,
                        second_text=b.text,
                        differing_positions=differences,
                    )
                )
                match_id += 1

        # Strongest/longest first.
        candidates.sort(
            key=lambda m: (
                m.similarity,
                len(m.first_text.split()),
                -m.first_start,
            ),
            reverse=True,
        )

        # Reduce redundant matches: keep a small representative set.
        selected: List[PhraseMatch] = []
        seen_pairs = set()

        for match in candidates:
            key = (
                round(match.first_start, 2),
                round(match.second_start, 2),
                match.first_text,
                match.second_text,
            )
            if key in seen_pairs:
                continue

            selected.append(match)
            seen_pairs.add(key)

            if len(selected) >= 100:
                break

        return selected

    def analyze_report(self, report: Dict[str, Any]) -> Dict[str, Any]:
        matches = self.find_matches(report)

        return {
            "engine": "LyricPhraseMatcher",
            "version": "1.0.0",
            "settings": {
                "min_phrase_words": self.min_phrase_words,
                "max_phrase_words": self.max_phrase_words,
                "min_similarity": self.min_similarity,
                "min_confidence": self.min_confidence,
            },
            "match_count": len(matches),
            "matches": [asdict(m) for m in matches],
        }

    def analyze_file(self, input_path: str, output_path: str) -> Dict[str, Any]:
        with open(input_path, "r", encoding="utf-8") as handle:
            report = json.load(handle)

        result = self.analyze_report(report)

        with open(output_path, "w", encoding="utf-8") as handle:
            json.dump(result, handle, ensure_ascii=False, indent=2)

        return result