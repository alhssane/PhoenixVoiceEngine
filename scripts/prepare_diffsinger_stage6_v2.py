from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path


def read_csv(path: Path):
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def main() -> int:
    ap = argparse.ArgumentParser(description="Phoenix generic DiffSinger config builder")
    ap.add_argument("--raw", required=True)
    ap.add_argument("--diffsinger", required=True)
    ap.add_argument("--config", required=True)
    ap.add_argument("--binary", required=True)
    ap.add_argument("--speaker", required=True)
    ap.add_argument("--language", default="ar")
    args = ap.parse_args()

    raw_root = Path(args.raw).resolve()
    ds = Path(args.diffsinger).resolve()
    config = Path(args.config).resolve()
    binary = Path(args.binary).resolve()
    raw = raw_root / "raw" if (raw_root / "raw" / "transcriptions.csv").exists() else raw_root
    csv_path = raw / "transcriptions.csv"
    wavs = raw / "wavs"
    phones_path = raw_root / "phonemes.txt"
    report_path = raw_root / "dataset_stage5.json"

    for path in (csv_path, wavs, phones_path, report_path):
        if not path.exists():
            raise FileNotFoundError(f"Missing required Stage5 artifact: {path}")
    if not (ds / "configs" / "acoustic.yaml").exists():
        raise FileNotFoundError(f"DiffSinger acoustic config not found: {ds / 'configs' / 'acoustic.yaml'}")

    report = json.loads(report_path.read_text(encoding="utf-8"))
    if report.get("status") != "RAW_DATASET_VALIDATED":
        raise RuntimeError("Stage5 report is not RAW_DATASET_VALIDATED.")
    rows = read_csv(csv_path)
    if len(rows) != report.get("segment_count"):
        raise RuntimeError("transcriptions.csv count does not match Stage5 report.")

    phones = [line.strip() for line in phones_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    special = {"SP", "AP", "<PAD>"}
    extra = [phone for phone in phones if phone not in special]
    if not extra:
        raise RuntimeError("No canonical Arabic phones found in Stage5 phonemes.txt")

    for row in rows:
        seq = row["ph_seq"].split()
        dur = row["ph_dur"].split()
        if len(seq) != len(dur):
            raise RuntimeError(f"Phone/duration mismatch in {row['name']}")
        bad = [phone for phone in seq if phone not in phones]
        if bad:
            raise RuntimeError(f"Unsupported phones in {row['name']}: {sorted(set(bad))}")
        if not (wavs / f"{row['name']}.wav").exists():
            raise FileNotFoundError(f"Missing WAV: {wavs / (row['name'] + '.wav')}")

    test_prefixes = [row["name"] for row in rows[-2:]] if len(rows) >= 3 else [rows[-1]["name"]]
    dictionary = config.parent / "phoenix_arabic_dictionary.txt"
    dictionary.parent.mkdir(parents=True, exist_ok=True)
    dictionary.write_text("PHOENIX_ARABIC\t" + " ".join(extra) + "\n", encoding="utf-8")

    lines = [
        "base_config:",
        "  - configs/acoustic.yaml",
        "",
        "dictionaries:",
        f"  {args.language}: {dictionary.as_posix()}",
        "extra_phonemes:",
        *[f"  - {phone}" for phone in extra],
        "merged_phoneme_groups: []",
        "",
        "datasets:",
        "  - raw_data_dir: " + raw.as_posix(),
        "    speaker: " + args.speaker,
        "    spk_id: 0",
        "    language: " + args.language,
        "    test_prefixes:",
        *[f"      - {name}" for name in test_prefixes],
        "",
        "binary_data_dir: " + binary.as_posix(),
        "binarization_args:",
        "  shuffle: false",
        "  num_workers: 0",
        "use_lang_id: false",
        "num_lang: 1",
        "use_spk_id: false",
        "num_spk: 1",
        "val_with_vocoder: false",
        "hnsep: world",
        "hnsep_ckpt: null",
        "use_key_shift_embed: false",
        "use_speed_embed: false",
        "",
    ]
    config.parent.mkdir(parents=True, exist_ok=True)
    config.write_text("\n".join(lines), encoding="utf-8")
    result = {
        "status": "STAGE6_GENERIC_CONFIG_READY",
        "speaker": args.speaker,
        "language": args.language,
        "segments": len(rows),
        "phoneme_count": len(phones),
        "dictionary": str(dictionary),
        "raw_data_dir": str(raw),
        "config": str(config),
        "binary_data_dir": str(binary),
        "training_allowed": False,
        "next_gate": "DIFFSINGER_BINARIZE",
    }
    (config.parent / "stage6_config_report.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
