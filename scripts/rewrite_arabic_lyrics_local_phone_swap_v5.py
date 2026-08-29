from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.arabic.g2p_frontend import PhoenixArabicG2PFrontend

NORMALIZE = {"aa": "a", "ii": "i", "uu": "u"}


def norm_phone(p: str) -> str:
    return NORMALIZE.get(p, p)


def load_ds(path: Path) -> tuple[list[dict], dict]:
    payload = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(payload, list) or len(payload) != 1:
        raise RuntimeError("V5 requires a DS file with exactly one segment.")
    seg = payload[0]
    for key in ("ph_seq", "ph_dur", "ph_num", "note_seq", "note_dur", "f0_seq", "f0_timestep"):
        if key not in seg:
            raise RuntimeError(f"Reference DS is missing required field: {key}")
    return payload, seg


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Controlled local phone substitution inside the original DS timeline."
    )
    ap.add_argument("--reference-ds", required=True, type=Path)
    ap.add_argument("--output", type=Path)
    ap.add_argument("--text", default=None, help="Arabic replacement text.")
    ap.add_argument("--start-phone", type=int, default=None, help="0-based inclusive phone index.")
    ap.add_argument("--inspect", action="store_true")
    args = ap.parse_args()

    payload, seg = load_ds(args.reference_ds.resolve())
    phones = str(seg["ph_seq"]).split()
    durations = [float(x) for x in str(seg["ph_dur"]).split()]
    if len(phones) != len(durations):
        raise RuntimeError("ph_seq/ph_dur length mismatch.")

    if args.inspect:
        rows = []
        t = 0.0
        for i, (p, d) in enumerate(zip(phones, durations)):
            rows.append({
                "index": i,
                "phone": p,
                "duration_sec": round(d, 6),
                "start_sec": round(t, 6),
                "end_sec": round(t + d, 6),
            })
            t += d
        print(json.dumps({
            "status": "LOCAL_SWAP_INSPECTION",
            "phone_count": len(phones),
            "duration_sec": round(t, 6),
            "phones": rows,
        }, ensure_ascii=False, indent=2))
        return 0

    if args.text is None or args.start_phone is None or args.output is None:
        raise RuntimeError("Use --inspect, or provide --text, --start-phone and --output.")

    frontend = PhoenixArabicG2PFrontend()
    result = frontend.convert(args.text)
    replacement = [norm_phone(p) for p in result.canonical_phones if p != "|"]
    if not replacement:
        raise RuntimeError("G2P produced no replacement phones.")

    start = args.start_phone
    end = start + len(replacement)
    if start < 0 or end > len(phones):
        raise RuntimeError(
            f"Replacement span {start}:{end} is outside phone sequence length {len(phones)}."
        )

    original = phones[start:end]
    # Keep every duration, note, ph_num and F0 value untouched. This isolates
    # the checkpoint's ability to respond to changed text embeddings.
    new_phones = list(phones)
    new_phones[start:end] = replacement

    out = dict(seg)
    out["text"] = args.text
    out["ph_seq"] = " ".join(new_phones)
    out["rewrite_engine"] = "phoenix_local_phone_swap_v5"
    out["rewrite_reference"] = "all_timing_notes_f0_and_ph_num_unchanged"
    out["local_swap"] = {
        "start_phone": start,
        "end_phone_exclusive": end,
        "original_phones": original,
        "replacement_phones": replacement,
        "duration_sec": round(sum(durations[start:end]), 6),
    }

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps([out], ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print(json.dumps({
        "status": "LOCAL_PHONE_SWAP_V5_READY",
        "output": str(args.output.resolve()),
        "start_phone": start,
        "end_phone_exclusive": end,
        "original_phones": original,
        "replacement_phones": replacement,
        "replacement_phone_count": len(replacement),
        "span_duration_sec": round(sum(durations[start:end]), 6),
        "timing_unchanged": True,
        "notes_unchanged": True,
        "f0_unchanged": True,
        "ph_num_unchanged": True,
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
