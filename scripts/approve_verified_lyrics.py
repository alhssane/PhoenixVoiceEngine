from __future__ import annotations

import argparse
import json
from pathlib import Path


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Validate and promote a manually verified singing-lyrics file to a training-ready master."
    )
    ap.add_argument("--verified-json", required=True)
    ap.add_argument("--output", required=True)
    args = ap.parse_args()

    src = Path(args.verified_json).resolve()
    out = Path(args.output).resolve()
    payload = json.loads(src.read_text(encoding="utf-8"))

    errors: list[dict] = []
    approved_gaps = 0
    approved_segments = 0
    total_gaps = len(payload.get("gaps", []))

    for gap in payload.get("gaps", []):
        segments = gap.get("segments") or []
        if not segments:
            errors.append({"gap_index": gap.get("gap_index"), "reason": "no_segments"})
            continue

        gap_ok = bool(gap.get("approved"))
        for seg in segments:
            start = float(seg.get("start_sec", 0.0))
            end = float(seg.get("end_sec", 0.0))
            text = str(seg.get("verified_text", "")).strip()
            approved = bool(seg.get("approved"))
            if end <= start:
                errors.append({"gap_index": gap.get("gap_index"), "segment_index": seg.get("segment_index"), "reason": "non_positive_timing"})
            if not text:
                errors.append({"gap_index": gap.get("gap_index"), "segment_index": seg.get("segment_index"), "reason": "missing_verified_text"})
            if not approved:
                errors.append({"gap_index": gap.get("gap_index"), "segment_index": seg.get("segment_index"), "reason": "segment_not_approved"})
            if approved and text and end > start:
                approved_segments += 1
            else:
                gap_ok = False
        if gap_ok:
            approved_gaps += 1

    training_allowed = total_gaps > 0 and approved_gaps == total_gaps and not errors
    status = "VERIFIED_LYRICS_READY" if training_allowed else "VERIFICATION_INCOMPLETE"

    out_payload = dict(payload)
    out_payload["status"] = status
    out_payload["training_allowed"] = training_allowed
    out_payload["verified_gap_count"] = approved_gaps
    out_payload["verified_segment_count"] = approved_segments
    out_payload["validation_errors"] = errors
    out_payload["next_gate"] = "STAGE1_FULL_REBUILD" if training_allowed else "HUMAN_VERIFY_AND_APPROVE_MISSING_LYRICS"

    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(out_payload, ensure_ascii=False, indent=2), encoding="utf-8")

    print(json.dumps({
        "status": status,
        "gap_count": total_gaps,
        "verified_gap_count": approved_gaps,
        "verified_segment_count": approved_segments,
        "validation_error_count": len(errors),
        "training_allowed": training_allowed,
        "output": str(out),
        "next_gate": out_payload["next_gate"],
    }, ensure_ascii=False, indent=2))
    return 0 if training_allowed else 2


if __name__ == "__main__":
    raise SystemExit(main())
