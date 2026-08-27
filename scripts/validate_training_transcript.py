from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any


# Known contamination seen in earlier PhoenixVoiceEngine datasets.
# This list is deliberately small and exact: the validator should block
# known non-training inserts without attempting to rewrite lyrics.
FORBIDDEN_PHRASES = (
    "اشتركوا في القناة",
    "اشتركوا بالقناة",
)


def fix_mojibake(text: str) -> str:
    """Repair the specific UTF-8/Windows-1256 mojibake seen in project JSON."""
    if not isinstance(text, str):
        return text
    try:
        return text.encode("cp1256").decode("utf-8")
    except (UnicodeEncodeError, UnicodeDecodeError):
        return text


def load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except UnicodeDecodeError as exc:
        raise RuntimeError(f"UTF-8 decode failed: {path}: {exc}") from exc
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"Invalid JSON: {path}: {exc}") from exc


def main() -> int:
    ap = argparse.ArgumentParser(description="Validate Phoenix DiffSinger training transcript.")
    ap.add_argument("--words-json", required=True)
    ap.add_argument("--audio-duration", type=float, required=False)
    ap.add_argument("--repair-mojibake", action="store_true")
    ap.add_argument("--output", required=False)
    args = ap.parse_args()

    words_path = Path(args.words_json).resolve()
    if not words_path.exists():
        raise FileNotFoundError(f"Words JSON not found: {words_path}")

    data = load_json(words_path)
    if not isinstance(data, list) or not data:
        raise RuntimeError("Training transcript must be a non-empty JSON list.")

    issues: list[dict[str, Any]] = []
    normalized: list[dict[str, Any]] = []
    last_end = -math.inf

    for idx, item in enumerate(data):
        if not isinstance(item, dict):
            issues.append({"type": "invalid_record", "index": idx})
            continue

        raw_word = item.get("word")
        if not isinstance(raw_word, str) or not raw_word.strip():
            issues.append({"type": "missing_word", "index": idx})
            continue

        word = fix_mojibake(raw_word) if args.repair_mojibake else raw_word.strip()
        word = word.strip()

        try:
            start = float(item["start"])
            end = float(item["end"])
        except (KeyError, TypeError, ValueError) as exc:
            issues.append({"type": "invalid_timing", "index": idx, "word": word, "error": str(exc)})
            continue

        if not (math.isfinite(start) and math.isfinite(end)):
            issues.append({"type": "non_finite_timing", "index": idx, "word": word})
        if end < start:
            issues.append({"type": "negative_duration", "index": idx, "word": word, "start": start, "end": end})
        if end <= start:
            issues.append({"type": "zero_or_negative_duration", "index": idx, "word": word, "start": start, "end": end})

        if start < last_end - 1e-6:
            issues.append({"type": "overlap_or_out_of_order", "index": idx, "word": word, "start": start, "previous_end": last_end})

        if any(phrase in word for phrase in FORBIDDEN_PHRASES):
            issues.append({"type": "forbidden_training_text", "index": idx, "word": word})

        last_end = max(last_end, end)
        normalized.append({"word": word, "start": start, "end": end, "duration": end - start})

    if args.audio_duration is not None:
        if last_end > args.audio_duration + 0.05:
            issues.append({"type": "timing_exceeds_audio", "last_end": last_end, "audio_duration": args.audio_duration})

    report = {
        "status": "TRANSCRIPT_REJECTED" if issues else "TRANSCRIPT_VALID",
        "words_path": str(words_path),
        "word_count": len(normalized),
        "last_word_end_sec": last_end if normalized else None,
        "audio_duration_sec": args.audio_duration,
        "issue_count": len(issues),
        "issues": issues,
        "forbidden_phrases": list(FORBIDDEN_PHRASES),
        "repair_mode": bool(args.repair_mojibake),
        "training_allowed": not issues,
    }

    if args.output:
        out = Path(args.output).resolve()
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    print(json.dumps(report, ensure_ascii=False, indent=2))

    if issues:
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
