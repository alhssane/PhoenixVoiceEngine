from __future__ import annotations

import json
import math
import re
from pathlib import Path
from typing import Any

ARABIC_RE = re.compile(r"[\u0600-\u06ff\u0750-\u077f\u08a0-\u08ff]")
_ARABIC_PRESENTATION_RE = re.compile(r"[\ufb50-\ufdff\ufe70-\ufeff]")


def _cp1256_utf8_repair(text: str) -> str:
    """Repair the UTF-8/Windows-1256 mojibake seen in legacy Phoenix JSON."""
    try:
        repaired = text.encode("cp1256").decode("utf-8")
    except (UnicodeEncodeError, UnicodeDecodeError):
        return text
    return repaired


def _score_arabic_text(text: str) -> tuple[int, int, int]:
    arabic = len(ARABIC_RE.findall(text))
    presentation = len(_ARABIC_PRESENTATION_RE.findall(text))
    # Known mojibake punctuation characters strongly indicate a bad decode.
    bad = sum(text.count(ch) for ch in ("¨", "§", "†", "‡", "‰", "Š", "Œ", "™", "›", "œ"))
    return arabic, presentation, -bad


def repair_mojibake(text: str) -> str:
    """Repair known Arabic mojibake only when the candidate is clearly better."""
    if not isinstance(text, str) or not text:
        return text
    candidate = _cp1256_utf8_repair(text)
    if candidate == text:
        return text
    return candidate if _score_arabic_text(candidate) > _score_arabic_text(text) else text


def normalize_arabic(text: str) -> str:
    """Return canonical UTF-8 Arabic text for Phoenix transcript stages."""
    text = repair_mojibake(str(text)).strip()
    # Remove Arabic combining marks/tatweel without altering letters.
    text = re.sub(r"[\u064b-\u065f\u0670\u06d6-\u06ed]", "", text)
    text = text.replace("ـ", "")
    text = text.replace("ظ€", "")
    text = re.sub(r"\s+", " ", text)
    return text


def canonicalize_words(data: Any) -> list[dict[str, Any]]:
    """Canonicalize a Phoenix timed-word list without changing timings."""
    if not isinstance(data, list) or not data:
        raise ValueError("Training transcript must be a non-empty JSON list")

    result: list[dict[str, Any]] = []
    for idx, item in enumerate(data):
        if not isinstance(item, dict):
            raise ValueError(f"Transcript item {idx} is not an object")
        word = normalize_arabic(item.get("word", ""))
        if not word:
            raise ValueError(f"Transcript item {idx} has an empty word")
        start = float(item["start"])
        end = float(item["end"])
        if not (math.isfinite(start) and math.isfinite(end)):
            raise ValueError(f"Transcript item {idx} has non-finite timing")
        out = dict(item)
        out["word"] = word
        out["start"] = start
        out["end"] = end
        out["duration"] = end - start
        result.append(out)
    return result


def load_words(path: Path) -> list[dict[str, Any]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    return canonicalize_words(payload)


def write_words(path: Path, words: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(words, ensure_ascii=False, indent=2), encoding="utf-8")
