from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.arabic.transcript_contract import load_words, normalize_arabic


START_COLUMNS = ("start", "start_sec", "segment_start", "begin")
END_COLUMNS = ("end", "end_sec", "segment_end", "finish")
WORD_COLUMNS = ("words", "text", "lyrics")


def pick_column(fieldnames: list[str], candidates: tuple[str, ...], label: str) -> str:
    for candidate in candidates:
        if candidate in fieldnames:
            return candidate
    raise RuntimeError(f"Stage1 manifest is missing a {label} column. Fields: {fieldnames}")


def main() -> int:
    ap = argparse.ArgumentParser(description="Enforce the canonical UTF-8 transcript on the Stage1 segment manifest.")
    ap.add_argument("--stage1", required=True)
    ap.add_argument("--words-json", required=True)
    args = ap.parse_args()

    stage1 = Path(args.stage1).resolve()
    words_path = Path(args.words_json).resolve()
    manifest_path = stage1 / "raw" / "segment_manifest.csv"
    if not manifest_path.is_file():
        raise FileNotFoundError(f"Stage1 manifest not found: {manifest_path}")

    words = load_words(words_path)
    with manifest_path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        fields = list(reader.fieldnames or [])

    if not rows:
        raise RuntimeError("Stage1 manifest is empty")

    start_col = pick_column(fields, START_COLUMNS, "start")
    end_col = pick_column(fields, END_COLUMNS, "end")
    word_col = pick_column(fields, WORD_COLUMNS, "word/text")

    changed = 0
    for row in rows:
        start = float(row[start_col])
        end = float(row[end_col])
        overlapping = [
            w["word"]
            for w in words
            if float(w["end"]) > start + 1e-6 and float(w["start"]) < end - 1e-6
        ]
        canonical = " ".join(overlapping)
        if not canonical:
            canonical = normalize_arabic(row.get(word_col, ""))
        if row.get(word_col, "") != canonical:
            row[word_col] = canonical
            changed += 1

    with manifest_path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)

    print({
        "status": "STAGE1_TRANSCRIPT_CANONICALIZED",
        "manifest": str(manifest_path),
        "canonical_words": str(words_path),
        "segment_count": len(rows),
        "changed_rows": changed,
    })
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
