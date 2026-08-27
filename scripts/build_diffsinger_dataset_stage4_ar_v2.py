from __future__ import annotations

import argparse
import csv
import json
import shutil
from pathlib import Path

import sys
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.arabic.phoneme_contract import CANONICAL_PHONES, validate_phone_sequence

SPECIAL = {"SP", "AP", "<PAD>"}
NORMALIZE = {"aa": "a", "ii": "i", "uu": "u"}
WORD_BOUNDARY = "|"


def normalize_aligned(phonemes, alignment):
    if len(phonemes) != len(alignment):
        raise RuntimeError("Stage3 phoneme/alignment length mismatch")
    out = []
    pending_boundary = 0.0
    for phone, item in zip(phonemes, alignment):
        duration = float(item.get("duration", 0.0))
        if duration < 0:
            raise RuntimeError(f"Negative phone duration: {phone!r}")
        if duration <= 0:
            continue
        if phone == WORD_BOUNDARY:
            pending_boundary += duration
            continue
        phone = NORMALIZE.get(phone, phone)
        duration += pending_boundary
        pending_boundary = 0.0
        if out and out[-1]["phone"] == phone and phone in {"a", "i", "u"}:
            out[-1]["duration"] += duration
        else:
            out.append({"phone": phone, "duration": duration})
    if pending_boundary > 0 and out:
        out[-1]["duration"] += pending_boundary
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description="Phoenix Stage4: canonical Arabic phone-set dataset")
    ap.add_argument("--stage1", required=True)
    ap.add_argument("--stage3", required=True)
    ap.add_argument("--output", required=True)
    args = ap.parse_args()

    stage1 = Path(args.stage1).resolve()
    stage3 = Path(args.stage3).resolve()
    output = Path(args.output).resolve()
    report_path = stage3 / "dataset_stage3.json"
    if not report_path.exists():
        raise FileNotFoundError(report_path)
    report = json.loads(report_path.read_text(encoding="utf-8"))
    if report.get("status") != "STAGE3_CANONICAL_ALIGNED":
        raise RuntimeError("Stage3 canonical alignment is not complete; refusing Stage4.")

    output.mkdir(parents=True, exist_ok=True)
    wavs = output / "raw" / "wavs"
    wavs.mkdir(parents=True, exist_ok=True)
    phones_dir = stage3 / "phones"
    rows = []
    phone_set = set(SPECIAL)

    for phone_json in sorted(phones_dir.glob("*.json")):
        payload = json.loads(phone_json.read_text(encoding="utf-8"))
        normalized = normalize_aligned(payload["phonemes"], payload["alignment"])
        normalized = [item for item in normalized if item["duration"] > 0]
        if not normalized:
            raise RuntimeError(f"No usable canonical phonemes after normalization: {phone_json.name}")
        phones = [item["phone"] for item in normalized]
        validate_phone_sequence(phones, allowed=CANONICAL_PHONES - {"|"})
        phone_set.update(phones)
        name = payload["name"]
        src = stage1 / "raw" / "wavs" / f"{name}.wav"
        if not src.exists():
            raise FileNotFoundError(f"Missing Stage1 source wav: {src}")
        shutil.copy2(src, wavs / src.name)
        rows.append({"name": name, "ph_seq": " ".join(phones), "ph_dur": " ".join(f"{max(0.001, item['duration']):.4f}" for item in normalized)})

    rows.sort(key=lambda item: item["name"])
    csv_path = output / "raw" / "transcriptions.csv"
    with csv_path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["name", "ph_seq", "ph_dur"])
        writer.writeheader()
        writer.writerows(rows)

    core = sorted(phone_set - SPECIAL)
    phonemes = ["SP", "AP", "<PAD>"] + core
    phones_path = output / "phonemes.txt"
    phones_path.write_text("\n".join(phonemes) + "\n", encoding="utf-8")
    meta = {
        "language": "ar",
        "name": "phoenix_arabic_canonical_v1",
        "phones": phonemes,
        "special": sorted(SPECIAL),
        "normalization": NORMALIZE,
        "source": "Stage3 canonical Arabic phoneme contract + CTC forced alignment",
        "strict_unknown_phone_policy": "reject",
    }
    (output / "phone_set.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    result = {
        "schema_version": "1.0",
        "status": "ARABIC_CANONICAL_PHONESET_READY",
        "segment_count": len(rows),
        "phoneme_count": len(phonemes),
        "phonemes": phonemes,
        "training_allowed": False,
        "next_gate": "DIFFSINGER_DATASET_BAKE_AND_PREPROCESS",
        "dataset": str(output),
        "phonemes_file": str(phones_path),
        "transcriptions": str(csv_path),
    }
    (output / "dataset_stage4_ar.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({k: result[k] for k in ("status", "segment_count", "phoneme_count", "training_allowed", "next_gate")}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
