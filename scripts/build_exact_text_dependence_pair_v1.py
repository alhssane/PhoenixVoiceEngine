from __future__ import annotations

import argparse
import copy
import hashlib
import json
from pathlib import Path
from typing import Any


def split_tokens(value: Any) -> list[str]:
    return [x for x in str(value or "").split() if x]


def sha256_text(value: Any) -> str:
    return hashlib.sha256(str(value).encode("utf-8")).hexdigest()


def load_single_segment(path: Path) -> tuple[bool, dict[str, Any]]:
    payload = json.loads(path.read_text(encoding="utf-8-sig"))
    if isinstance(payload, list):
        if len(payload) != 1 or not isinstance(payload[0], dict):
            raise RuntimeError("Expected a DS object or a one-segment DS array.")
        return True, payload[0]
    if not isinstance(payload, dict):
        raise RuntimeError("Expected a DS object or a one-segment DS array.")
    return False, payload


def dump_segment(path: Path, segment: dict[str, Any], as_array: bool) -> None:
    payload: Any = [segment] if as_array else segment
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Build an exact control/mutant DS pair. The control is a semantic copy "
            "of the known-good DS; the mutant changes only selected phone symbols."
        )
    )
    parser.add_argument("--reference-ds", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--start-phone", type=int, default=10)
    parser.add_argument("--expect", default="n f i")
    parser.add_argument("--replace", default="n u r")
    args = parser.parse_args()

    reference = args.reference_ds.resolve()
    output_dir = args.output_dir.resolve()
    if not reference.is_file():
        raise FileNotFoundError(reference)

    as_array, original = load_single_segment(reference)
    required = ("ph_seq", "ph_dur", "f0_seq", "f0_timestep")
    missing = [key for key in required if key not in original]
    if missing:
        raise RuntimeError(f"Reference DS is missing required fields: {missing}")

    phones = split_tokens(original["ph_seq"])
    durations = split_tokens(original["ph_dur"])
    if len(phones) != len(durations):
        raise RuntimeError(
            f"Reference ph_seq/ph_dur mismatch: {len(phones)} vs {len(durations)}"
        )

    expected = split_tokens(args.expect)
    replacement = split_tokens(args.replace)
    if not expected or len(expected) != len(replacement):
        raise RuntimeError("--expect and --replace must have the same non-zero phone count.")

    start = args.start_phone
    end = start + len(expected)
    if start < 0 or end > len(phones):
        raise RuntimeError(f"Phone span {start}:{end} is outside 0:{len(phones)}")
    observed = phones[start:end]
    if observed != expected:
        raise RuntimeError(
            f"Reference guard failed at {start}:{end}: expected {expected}, observed {observed}. "
            "No files were written."
        )

    control = copy.deepcopy(original)
    mutant = copy.deepcopy(original)
    mutant_phones = list(phones)
    mutant_phones[start:end] = replacement
    mutant["ph_seq"] = " ".join(mutant_phones)

    output_dir.mkdir(parents=True, exist_ok=True)
    control_path = output_dir / "control_exact.ds"
    mutant_path = output_dir / "mutant_n_u_r.ds"
    manifest_path = output_dir / "pair_manifest.json"
    dump_segment(control_path, control, as_array)
    dump_segment(mutant_path, mutant, as_array)

    immutable_fields = [
        key for key in original.keys()
        if key not in {"ph_seq", "text", "rewrite_engine", "rewrite_reference", "local_swap"}
    ]
    changed_fields = sorted(
        key for key in set(control) | set(mutant)
        if control.get(key) != mutant.get(key)
    )

    immutable_mismatches = [
        key for key in immutable_fields if control.get(key) != mutant.get(key)
    ]
    if changed_fields != ["ph_seq"] or immutable_mismatches:
        raise RuntimeError(
            f"Isolation invariant failed: changed_fields={changed_fields}, "
            f"immutable_mismatches={immutable_mismatches}"
        )

    manifest = {
        "status": "EXACT_TEXT_DEPENDENCE_PAIR_READY",
        "reference_ds": str(reference),
        "control_ds": str(control_path),
        "mutant_ds": str(mutant_path),
        "phone_count": len(phones),
        "start_phone": start,
        "end_phone_exclusive": end,
        "original_phones": observed,
        "replacement_phones": replacement,
        "changed_fields": changed_fields,
        "ph_dur_sha256_control": sha256_text(control["ph_dur"]),
        "ph_dur_sha256_mutant": sha256_text(mutant["ph_dur"]),
        "f0_seq_sha256_control": sha256_text(control["f0_seq"]),
        "f0_seq_sha256_mutant": sha256_text(mutant["f0_seq"]),
        "note_seq_sha256_control": sha256_text(control.get("note_seq", "")),
        "note_seq_sha256_mutant": sha256_text(mutant.get("note_seq", "")),
        "note_dur_sha256_control": sha256_text(control.get("note_dur", "")),
        "note_dur_sha256_mutant": sha256_text(mutant.get("note_dur", "")),
        "isolation_pass": True,
    }
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(json.dumps(manifest, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
