from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable


@dataclass(frozen=True)
class WordTimelineItem:
    word: str
    start: float
    end: float
    duration: float
    index: int


class WordReplacementEngine:
    """Apply deterministic word replacements to an extracted word timeline."""

    VERSION = "2.0.0"

    def load_timeline(self, timeline_path: str | Path) -> list[WordTimelineItem]:
        import json

        data = __import__("json").loads(Path(timeline_path).read_text(encoding="utf-8"))
        if not isinstance(data, list):
            raise ValueError("Word timeline must be a JSON list")
        items: list[WordTimelineItem] = []
        for index, item in enumerate(data):
            if not isinstance(item, dict):
                raise ValueError(f"Timeline item {index} is not an object")
            start = float(item["start"])
            end = float(item["end"])
            if start < 0 or end < start:
                raise ValueError(f"Invalid timing at timeline item {index}")
            word = str(item.get("word", "")).strip()
            if word:
                items.append(WordTimelineItem(word, start, end, max(0.0, end - start), index))
        return items

    def replace(
        self,
        original_word: str,
        replacement_word: str,
        *,
        timeline_path: str | Path,
        occurrence: int = 0,
    ) -> dict[str, Any]:
        original, replacement = original_word.strip(), replacement_word.strip()
        if not original or not replacement:
            raise ValueError("Both original_word and replacement_word are required")
        if occurrence < 0:
            raise ValueError("occurrence must be >= 0")
        items = self.load_timeline(timeline_path)
        matches = [item for item in items if item.word == original]
        if occurrence >= len(matches):
            return {"status": "WORD_NOT_FOUND", "matches": len(matches)}
        target = matches[occurrence]
        target_text = " ".join(replacement if item is target else item.word for item in items)
        return {
            "status": "READY",
            "original_word": original,
            "replacement_word": replacement,
            "occurrence": occurrence,
            "start": target.start,
            "end": target.end,
            "duration": target.duration,
            "target_text": target_text,
            "timeline_index": target.index,
        }

    def build_target_text(
        self,
        timeline: Iterable[dict[str, Any] | WordTimelineItem],
        replacements: dict[str, str],
    ) -> str:
        words: list[str] = []
        for item in timeline:
            word = item.word if isinstance(item, WordTimelineItem) else str(item.get("word", ""))
            if word:
                words.append(replacements.get(word, word))
        return " ".join(words)
