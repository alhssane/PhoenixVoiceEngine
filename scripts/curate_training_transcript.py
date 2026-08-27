from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

FORBIDDEN_SEQUENCES = {
    ("اشتركوا", "في", "القناة"),
    ("اشتركوا", "بالقناة"),
}


def fix_mojibake(text: str) -> str:
    try:
        return text.encode("cp1256").decode("utf-8")
    except (UnicodeEncodeError, UnicodeDecodeError):
        return text


def main() -> int:
    ap = argparse.ArgumentParser(description="Create a safe candidate transcript without inventing lyrics.")
    ap.add_argument("--words-json", required=True)
    ap.add_argument("--output", required=True)
    ap.add_argument("--audio-duration", type=float, required=False)
    args = ap.parse_args()

    src = Path(args.words_json).resolve()
    out = Path(args.output).resolve()
    data = json.loads(src.read_text(encoding="utf-8"))
    if not isinstance(data, list) or not data:
        raise RuntimeError("Transcript must be a non-empty list.")

    normalized: list[dict[str, Any]] = []
    rejected: list[dict[str, Any]] = []

    for i, item in enumerate(data):
        if not isinstance(item, dict):
            rejected.append({"index": i, "reason": "invalid_record"})
            continue
        raw = item.get("word")
        if not isinstance(raw, str) or not raw.strip():
            rejected.append({"index": i, "reason": "missing_word"})
            continue
        word = fix_mojibake(raw.strip())
        try:
            start = float(item["start"])
            end = float(item["end"])
        except (KeyError, TypeError, ValueError):
            rejected.append({"index": i, "reason": "invalid_timing", "word": word})
            continue
        normalized.append({"word": word, "start": start, "end": end, "duration": end - start, "source_index": i})

    # Reject known contamination as a sequence, not merely as a single token.
    rejected_indices: set[int] = set()
    words = [r["word"] for r in normalized]
    for start in range(len(words)):
        for seq in FORBIDDEN_SEQUENCES:
            if tuple(words[start:start + len(seq)]) == seq:
                end = start + len(seq)
                rejected_indices.update(range(start, end))
                rejected.append({
                    "source_start_index": normalized[start]["source_index"],
                    "source_end_index": normalized[end - 1]["source_index"],
                    "reason": "forbidden_training_sequence",
                    "words": list(seq),
                })

    candidate = []
    for idx, row in enumerate(normalized):
        if idx in rejected_indices:
            continue
        if row["end"] <= row["start"]:
            rejected.append({"index": row["source_index"], "reason": "zero_or_negative_duration", "word": row["word"]})
            continue
        if args.audio_duration is not None and row["start"] >= args.audio_duration:
            rejected.append({"index": row["source_index"], "reason": "outside_audio", "word": row["word"]})
            continue
        candidate.append(row)

    report = {
        "status": "CURATED_CANDIDATE_READY" if candidate else "CURATION_FAILED",
        "source": str(src),
        "audio_duration_sec": args.audio_duration,
        "source_word_count": len(data),
        "candidate_word_count": len(candidate),
        "rejected_count": len(rejected),
        "candidate": candidate,
        "rejected": rejected,
        "training_allowed": False,
        "note": "This tool only removes known contaminated/invalid records. It never invents missing lyrics or timing.",
        "next_gate": "VERIFY_MISSING_SINGING_TEXT_BEFORE_TRAINING",
    }

    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
