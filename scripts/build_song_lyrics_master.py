from __future__ import annotations

import argparse
import json
from pathlib import Path

FORBIDDEN = {"اشتركوا في القناة", "اشتركوا بالقناة"}


def fix_mojibake(text: str) -> str:
    try:
        return text.encode("cp1256").decode("utf-8")
    except (UnicodeEncodeError, UnicodeDecodeError):
        return text


def main() -> int:
    ap = argparse.ArgumentParser(description="Build an auditable master lyric manifest from verified source words.")
    ap.add_argument("--words-json", required=True)
    ap.add_argument("--output", required=True)
    ap.add_argument("--source-duration", type=float, required=True)
    args = ap.parse_args()

    src = Path(args.words_json).resolve()
    out = Path(args.output).resolve()
    data = json.loads(src.read_text(encoding="utf-8"))
    if not isinstance(data, list) or not data:
        raise RuntimeError("Source words JSON must be a non-empty list.")

    words = []
    rejected = []
    for i, item in enumerate(data):
        if not isinstance(item, dict):
            rejected.append({"index": i, "reason": "invalid_record"})
            continue
        raw = str(item.get("word", ""))
        word = fix_mojibake(raw).strip()
        start = float(item.get("start", 0.0))
        end = float(item.get("end", 0.0))
        if word in {"في", "القناة"} and i in {74, 75, 77, 78, 80, 81, 83, 84, 86, 87, 89, 90, 92, 93}:
            rejected.append({"index": i, "word": word, "reason": "known_contaminated_sequence"})
            continue
        if end <= start:
            rejected.append({"index": i, "word": word, "start": start, "end": end, "reason": "non_positive_duration"})
            continue
        if word in FORBIDDEN:
            rejected.append({"index": i, "word": word, "reason": "forbidden_phrase"})
            continue
        words.append({"word": word, "start": start, "end": end, "duration": end-start, "source_index": i, "source": "verified_source"})

    # Never claim full coverage automatically. Missing singing must be explicitly supplied later.
    report = {
        "schema_version": "phoenix-song-lyrics-master-v1",
        "source_words": str(src),
        "source_duration_sec": args.source_duration,
        "verified_word_count": len(words),
        "rejected_source_count": len(rejected),
        "verified_coverage_end_sec": max((x["end"] for x in words), default=0.0),
        "missing_singing_text_required": True,
        "training_allowed": False,
        "status": "MASTER_CANDIDATE_NEEDS_MISSING_LYRICS",
        "words": words,
        "rejected_source_entries": rejected,
        "manual_verification": {
            "required_for_gap_ranges": [
                [35.90, 36.54], [56.12, 59.78], [61.26, 92.32],
                [98.56, 121.92], [126.16, 162.50], [163.36, 183.74],
                [187.28, 217.06], [221.12, args.source_duration]
            ],
            "rule": "Only verified lyrics with real timing may be promoted to training status."
        }
    }
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({k: report[k] for k in ("status", "verified_word_count", "rejected_source_count", "verified_coverage_end_sec", "training_allowed", "missing_singing_text_required")}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
