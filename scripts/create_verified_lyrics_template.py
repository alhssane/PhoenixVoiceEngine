from __future__ import annotations

import argparse
import json
from pathlib import Path


def fix_mojibake(text: str) -> str:
    if not isinstance(text, str):
        return text
    try:
        return text.encode("cp1256").decode("utf-8")
    except (UnicodeEncodeError, UnicodeDecodeError):
        return text


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Create a human-verification template for missing singing lyrics."
    )
    ap.add_argument("--review-json", required=True)
    ap.add_argument("--output", required=True)
    args = ap.parse_args()

    review_path = Path(args.review_json).resolve()
    output_path = Path(args.output).resolve()
    review = json.loads(review_path.read_text(encoding="utf-8"))

    gaps = []
    for i, gap in enumerate(review.get("gaps", [])):
        draft = gap.get("draft_asr") or {}
        raw_segments = draft.get("segments") or []
        segments = []

        for j, seg in enumerate(raw_segments):
            start = float(gap["start_sec"]) + float(seg.get("start", 0.0))
            end = float(gap["start_sec"]) + float(seg.get("end", 0.0))
            if end <= start:
                continue
            segments.append(
                {
                    "segment_index": j,
                    "start_sec": start,
                    "end_sec": end,
                    "asr_candidate": fix_mojibake(seg.get("text", "")),
                    "verified_text": "",
                    "approved": False,
                }
            )

        # Keep a reviewable segment even when ASR produced no segment.
        if not segments:
            segments.append(
                {
                    "segment_index": 0,
                    "start_sec": float(gap["start_sec"]),
                    "end_sec": float(gap["end_sec"]),
                    "asr_candidate": "",
                    "verified_text": "",
                    "approved": False,
                }
            )

        gaps.append(
            {
                "gap_index": i,
                "start_sec": float(gap["start_sec"]),
                "end_sec": float(gap["end_sec"]),
                "duration_sec": float(gap["duration_sec"]),
                "classification": gap.get("classification", {}).get("likely_singing"),
                "segments": segments,
                "approved": False,
            }
        )

    payload = {
        "schema_version": "phoenix-song-verified-lyrics-v2",
        "status": "VERIFICATION_PENDING",
        "source_review": str(review_path),
        "rules": {
            "asr_candidate_is_not_final": True,
            "verified_text_must_be_human_checked": True,
            "approved_must_be_true_only_after_review": True,
            "all_singing_gaps_must_be_approved_before_training": True,
            "timing_must_be_verified_for_each_segment": True,
        },
        "gaps": gaps,
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print(
        json.dumps(
            {
                "status": payload["status"],
                "gap_count": len(gaps),
                "segment_count": sum(len(g["segments"]) for g in gaps),
                "output": str(output_path),
                "next_gate": "HUMAN_VERIFY_AND_APPROVE_MISSING_LYRICS",
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
