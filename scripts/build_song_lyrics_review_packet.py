from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Create an auditable lyrics-review packet for uncovered singing regions."
    )
    ap.add_argument("--coverage-json", required=True)
    ap.add_argument("--master-json", required=True)
    ap.add_argument("--output", required=True)
    ap.add_argument("--gap-asr-json", required=False)
    ap.add_argument("--gap-classification-json", required=False)
    args = ap.parse_args()

    coverage_path = Path(args.coverage_json).resolve()
    master_path = Path(args.master_json).resolve()
    output_path = Path(args.output).resolve()

    coverage = load_json(coverage_path)
    master = load_json(master_path)

    asr = None
    classification = None
    if args.gap_asr_json:
        p = Path(args.gap_asr_json).resolve()
        if p.exists():
            asr = load_json(p)
    if args.gap_classification_json:
        p = Path(args.gap_classification_json).resolve()
        if p.exists():
            classification = load_json(p)

    asr_by_file = {}
    if isinstance(asr, list):
        for item in asr:
            if isinstance(item, dict) and item.get("file"):
                asr_by_file[item["file"]] = {
                    "status": item.get("status"),
                    "text": item.get("text"),
                    "segments": item.get("segments", []),
                }

    class_by_file = {}
    if isinstance(classification, list):
        for item in classification:
            if isinstance(item, dict) and item.get("file"):
                class_by_file[item["file"]] = item

    gaps = []
    for gap in coverage.get("gaps", []):
        if not isinstance(gap, dict):
            continue
        start = float(gap.get("start_sec", 0.0))
        end = float(gap.get("end_sec", 0.0))
        duration = float(gap.get("duration_sec", max(0.0, end - start)))
        if not gap.get("likely_singing"):
            continue

        file_key = None
        for name, item in class_by_file.items():
            item_start = None
            item_end = None
            try:
                stem = Path(name).stem
                parts = stem.split("_")
                # Filename pattern: gap_00_61.36_92.22
                if len(parts) >= 4:
                    item_start = float(parts[-2])
                    item_end = float(parts[-1])
            except (ValueError, IndexError):
                pass
            if item_start is not None and abs(item_start - start) < 0.2 and abs(item_end - end) < 0.2:
                file_key = name
                break

        draft = asr_by_file.get(file_key or "")
        gaps.append(
            {
                "start_sec": start,
                "end_sec": end,
                "duration_sec": duration,
                "classification": gap,
                "draft_asr": draft,
                "verification_status": "REQUIRED",
                "promotion_rule": "Only human-verified lyrics with verified timing may enter the training master.",
            }
        )

    report = {
        "schema_version": "phoenix-song-lyrics-review-v1",
        "status": "LYRICS_REVIEW_REQUIRED" if gaps else "NO_MISSING_SINGING_GAPS",
        "coverage_json": str(coverage_path),
        "master_json": str(master_path),
        "verified_word_count": master.get("verified_word_count"),
        "missing_singing_gap_count": len(gaps),
        "missing_singing_duration_sec": sum(x["duration_sec"] for x in gaps),
        "training_allowed": False if gaps else bool(master.get("training_allowed", False)),
        "gaps": gaps,
        "review_rules": {
            "do_not_use_asr_as_final_lyrics": True,
            "do_not_invent_words": True,
            "do_not_retime_verified_words_without_evidence": True,
            "do_not_train_until_all_singing_gaps_are_verified": True,
        },
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({
        "status": report["status"],
        "missing_singing_gap_count": report["missing_singing_gap_count"],
        "missing_singing_duration_sec": report["missing_singing_duration_sec"],
        "training_allowed": report["training_allowed"],
        "output": str(output_path),
    }, ensure_ascii=False, indent=2))
    return 0 if not gaps else 2


if __name__ == "__main__":
    raise SystemExit(main())
