from __future__ import annotations

import argparse
import csv
import json
import shutil
from pathlib import Path

SPECIAL = {"SP", "AP", "<PAD>"}
NORMALIZE = {"aa": "a", "ii": "i", "uu": "u", "|": None}


def normalize_aligned(phonemes, alignment):
    out = []
    for phone, item in zip(phonemes, alignment):
        phone = NORMALIZE.get(phone, phone)
        if phone is None:
            continue
        duration = float(item.get("duration", 0.0))
        if out and out[-1]["phone"] == phone and phone in {"a", "i", "u"}:
            out[-1]["duration"] += duration
        else:
            out.append({"phone": phone, "duration": duration})
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--stage3", required=True)
    ap.add_argument("--output", required=True)
    args = ap.parse_args()

    stage3 = Path(args.stage3).resolve()
    output = Path(args.output).resolve()
    output.mkdir(parents=True, exist_ok=True)
    wavs = output / "raw" / "wavs"
    wavs.mkdir(parents=True, exist_ok=True)

    report = json.loads((stage3 / "dataset_stage3.json").read_text(encoding="utf-8"))
    if report.get("aligned_count") != report.get("segment_count") or report.get("status") != "STAGE3_ALIGNED":
        raise RuntimeError("Stage3 is not fully aligned; refusing to build the final Arabic phone-set dataset.")

    rows = []
    phone_set = set(SPECIAL)
    phones_dir = stage3 / "phones"
    stage1_wavs = stage3.parent / "freed_joud_diffsinger_stage1" / "raw" / "wavs"

    for phone_json in sorted(phones_dir.glob("*.json")):
        payload = json.loads(phone_json.read_text(encoding="utf-8"))
        normalized = normalize_aligned(payload["phonemes"], payload["alignment"])
        normalized = [x for x in normalized if x["duration"] > 0]
        if not normalized:
            raise RuntimeError(f"No usable phonemes after normalization: {phone_json.name}")
        for x in normalized:
            phone_set.add(x["phone"])
        rows.append({
            "name": payload["name"],
            "ph_seq": " ".join(x["phone"] for x in normalized),
            "ph_dur": " ".join(f"{max(0.001, x['duration']):.4f}" for x in normalized),
        })
        src = stage1_wavs / f"{payload['name']}.wav"
        if not src.exists():
            raise FileNotFoundError(f"Missing source wav: {src}")
        shutil.copy2(src, wavs / src.name)

    rows.sort(key=lambda r: r["name"])
    csv_path = output / "raw" / "transcriptions.csv"
    with csv_path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["name", "ph_seq", "ph_dur"])
        writer.writeheader()
        writer.writerows(rows)

    core = sorted(p for p in phone_set if p not in SPECIAL)
    phonemes = ["SP", "AP", "<PAD>"] + core
    phonemes_path = output / "phonemes.txt"
    phonemes_path.write_text("\n".join(phonemes) + "\n", encoding="utf-8")

    phone_meta = {
        "language": "ar",
        "name": "phoenix_arabic_native",
        "phones": phonemes,
        "special": sorted(SPECIAL),
        "normalization": NORMALIZE,
        "source": "Stage3 Arabic CTC forced alignment",
    }
    (output / "phone_set.json").write_text(json.dumps(phone_meta, ensure_ascii=False, indent=2), encoding="utf-8")

    result = {
        "schema_version": "0.3",
        "status": "ARABIC_PHONESET_READY",
        "segment_count": len(rows),
        "phoneme_count": len(phonemes),
        "phonemes": phonemes,
        "training_allowed": False,
        "next_gate": "DIFFSINGER_DATASET_BAKE_AND_PREPROCESS",
        "dataset": str(output),
        "phonemes_file": str(phonemes_path),
        "transcriptions": str(csv_path),
    }
    (output / "dataset_stage4_ar.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({k: result[k] for k in ("status", "segment_count", "phoneme_count", "training_allowed", "next_gate")}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
