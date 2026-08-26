from __future__ import annotations

import argparse
import csv
import json
import re
import shutil
from pathlib import Path

HEADER_WORDS = {"word", "words", "phoneme", "phonemes", "phone", "phones", "symbol", "symbols"}
SPECIAL = {"SP", "AP", "<PAD>"}


def discover_dictionaries(diff_root: Path) -> list[Path]:
    candidates = []
    for p in diff_root.rglob("*.txt"):
        n = p.name.lower()
        if "dictionary" in n or "phoneme" in n or "opencpop" in n:
            candidates.append(p)
    return sorted(candidates)


def parse_dictionary(path: Path) -> set[str]:
    """Parse common word->phoneme dictionary formats.

    The left-hand word is not a phoneme; all tokens on the right-hand side are.
    """
    phones: set[str] = set()
    try:
        for raw in path.read_text(encoding="utf-8", errors="ignore").splitlines():
            line = raw.strip()
            if not line or line.startswith("#"):
                continue
            fields = [f for f in re.split(r"\t+", line) if f.strip()]
            if len(fields) == 1:
                fields = line.split()
            if len(fields) < 2:
                continue
            rhs = []
            for field in fields[1:]:
                rhs.extend(field.split())
            for tok in rhs:
                tok = tok.strip()
                if tok and tok.lower() not in HEADER_WORDS:
                    phones.add(tok)
    except Exception:
        pass
    return phones


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--stage3", required=True)
    ap.add_argument("--diff-root", required=True)
    ap.add_argument("--output", required=True)
    args = ap.parse_args()

    stage3 = Path(args.stage3).resolve()
    diff_root = Path(args.diff_root).resolve()
    output = Path(args.output).resolve()

    report_path = stage3 / "dataset_stage3.json"
    csv_path = stage3 / "transcriptions.csv"
    if not report_path.exists() or not csv_path.exists():
        raise FileNotFoundError("Stage3 report/transcriptions.csv is missing")

    dictionaries = discover_dictionaries(diff_root)
    if not dictionaries:
        raise FileNotFoundError(f"No DiffSinger dictionary files found under {diff_root}")

    dict_union: set[str] = set(SPECIAL)
    dictionary_stats = []
    for d in dictionaries:
        phones = parse_dictionary(d)
        if phones:
            dict_union.update(phones)
            dictionary_stats.append({"path": str(d), "phone_count": len(phones)})

    rows = list(csv.DictReader(csv_path.open("r", encoding="utf-8-sig", newline="")))
    unsupported: dict[str, list[str]] = {}
    valid_rows = []
    for r in rows:
        phones = [p.strip() for p in r["ph_seq"].split() if p.strip()]
        missing = sorted({p for p in phones if p not in dict_union and p not in SPECIAL})
        if missing:
            unsupported[r["name"]] = missing
        else:
            valid_rows.append(r)

    raw = output / "raw"
    wavs = raw / "wavs"
    wavs.mkdir(parents=True, exist_ok=True)
    out_csv = raw / "transcriptions.csv"

    stage1_wavs = stage3.parent / "freed_joud_diffsinger_stage1" / "raw" / "wavs"
    copied = 0
    for r in valid_rows:
        src = stage1_wavs / f"{r['name']}.wav"
        if src.exists():
            shutil.copy2(src, wavs / src.name)
            copied += 1

    with out_csv.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["name", "ph_seq", "ph_dur"])
        writer.writeheader()
        writer.writerows(valid_rows)

    all_valid = len(valid_rows) == len(rows) and copied == len(rows)
    result = {
        "schema_version": "0.3",
        "status": "PHONESET_VALIDATED" if all_valid else "PHONESET_BLOCKED",
        "source_segments": len(rows),
        "valid_segments": len(valid_rows),
        "copied_wavs": copied,
        "dictionary_files": dictionary_stats,
        "dictionary_phone_count": len(dict_union),
        "unsupported": unsupported,
        "training_allowed": False,
        "next_gate": "DATASET_BAKE_AND_DIFFSINGER_PREPROCESS" if all_valid else "FIX_PHONESET_MISMATCH",
        "output": str(output),
    }
    (output / "dataset_stage4.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({k: result[k] for k in ("status", "source_segments", "valid_segments", "copied_wavs", "dictionary_phone_count", "training_allowed", "next_gate")}, ensure_ascii=False, indent=2))
    if unsupported:
        print("UNSUPPORTED_PHONES:")
        for name, missing in unsupported.items():
            print(f"- {name}: {', '.join(missing)}")


if __name__ == "__main__":
    main()
