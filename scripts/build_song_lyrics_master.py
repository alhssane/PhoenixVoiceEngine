from __future__ import annotations

import argparse
import json
from pathlib import Path

FORBIDDEN = (
    ("اشتركوا", "في", "القناة"),
)


def fix_mojibake(text: str) -> str:
    try:
        return text.encode("cp1256").decode("utf-8")
    except (UnicodeEncodeError, UnicodeDecodeError):
        return text


def main() -> int:
    ap = argparse.ArgumentParser(description="Build an auditable master lyric manifest from source words.")
    ap.add_argument("--words-json", required=True)
    ap.add_argument("--output", required=True)
    ap.add_argument("--source-duration", type=float, required=True)
    args = ap.parse_args()

    src = Path(args.words_json).resolve()
    out = Path(args.output).resolve()
    data = json.loads(src.read_text(encoding="utf-8"))
    if not isinstance(data, list) or not data:
        raise RuntimeError("Source words JSON must be a non-empty list.")

    normalized = []
    for i, item in enumerate(data):
        if not isinstance(item, dict):
            normalized.append({"source_index": i, "invalid": True})
            continue
        word = fix_mojibake(str(item.get("word", ""))).strip()
        try:
            start = float(item["start"])
            end = float(item["end"])
        except (KeyError, TypeError, ValueError):
            start = end = 0.0
        normalized.append({"source_index": i, "word": word, "start": start, "end": end, "duration": end - start})

    rejected_indices: set[int] = set()
    rejected = []

    # Reject known contaminated phrase sequences regardless of how they are split into records.
    for phrase in FORBIDDEN:
        n = len(phrase)
        for i in range(len(normalized) - n + 1):
            words = tuple(normalized[j].get("word", "") for j in range(i, i + n))
            if words == phrase:
                idxs = [normalized[j]["source_index"] for j in range(i, i + n)]
                rejected_indices.update(idxs)
                rejected.append({"source_start_index": idxs[0], "source_end_index": idxs[-1], "reason": "known_contaminated_sequence", "words": list(phrase)})

    for item in normalized:
        if item.get("source_index") in rejected_indices:
            continue
        if item.get("invalid"):
            rejected.append({"source_index": item["source_index"], "reason": "invalid_record"})
            rejected_indices.add(item["source_index"])
            continue
        if item["end"] <= item["start"]:
            rejected.append({"source_index": item["source_index"], "word": item["word"], "start": item["start"], "end": item["end"], "reason": "non_positive_duration"})
            rejected_indices.add(item["source_index"])

    words = [x for x in normalized if x.get("source_index") not in rejected_indices and not x.get("invalid")]

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
