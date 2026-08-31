from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

MODEL_VOWELS = {"a", "i", "u"}
DEFAULT_MIN_DURATION = 0.02


def parse_phone_sequence(value: str) -> list[str]:
    phones = [item for item in value.strip().split() if item]
    if not phones:
        raise argparse.ArgumentTypeError("Phone sequence must not be empty")
    return phones


def parse_float_sequence(value: str) -> list[float]:
    try:
        numbers = [float(item) for item in value.strip().split() if item]
    except ValueError as exc:
        raise argparse.ArgumentTypeError(f"Invalid float sequence: {value!r}") from exc
    if not numbers:
        raise argparse.ArgumentTypeError("Float sequence must not be empty")
    return numbers


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def load_ds(path: Path) -> tuple[dict[str, Any], bool]:
    payload = json.loads(path.read_text(encoding="utf-8-sig"))
    if isinstance(payload, list):
        if len(payload) != 1 or not isinstance(payload[0], dict):
            raise ValueError("Only a single-item DS list is supported")
        return dict(payload[0]), True
    if not isinstance(payload, dict):
        raise ValueError("DS root must be an object or a one-item list")
    return dict(payload), False


def dump_ds(path: Path, payload: dict[str, Any], was_list: bool) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    root: Any = [payload] if was_list else payload
    path.write_text(
        json.dumps(root, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def distribute_duration(
    total: float,
    replacement: list[str],
    weights: list[float] | None,
    minimum: float,
) -> list[float]:
    if total <= 0:
        raise ValueError(f"Replacement span duration must be positive, got {total}")
    if minimum <= 0:
        raise ValueError("Minimum phone duration must be positive")
    if total + 1e-12 < minimum * len(replacement):
        raise ValueError(
            "Span is too short for the replacement phone count: "
            f"total={total:.6f}, phones={len(replacement)}, minimum={minimum:.6f}"
        )

    if weights is None:
        weights = [2.0 if phone in MODEL_VOWELS else 1.0 for phone in replacement]
    if len(weights) != len(replacement):
        raise ValueError(
            f"Weight count mismatch: {len(weights)} != {len(replacement)}"
        )
    if any(weight <= 0 for weight in weights):
        raise ValueError("All duration weights must be positive")

    remaining = total - minimum * len(replacement)
    weight_sum = sum(weights)
    durations = [minimum + remaining * weight / weight_sum for weight in weights]
    durations[-1] += total - sum(durations)
    return durations


def replace_word(
    payload: dict[str, Any],
    start: int,
    expected: list[str],
    replacement: list[str],
    replacement_durations: list[float] | None = None,
    duration_weights: list[float] | None = None,
    minimum_duration: float = DEFAULT_MIN_DURATION,
    replacement_text: str | None = None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    phones = str(payload.get("ph_seq", "")).split()
    durations = [float(value) for value in str(payload.get("ph_dur", "")).split()]
    if not phones or not durations:
        raise ValueError("DS must contain non-empty ph_seq and ph_dur")
    if len(phones) != len(durations):
        raise ValueError(
            f"Phone/duration count mismatch: {len(phones)} != {len(durations)}"
        )
    if start < 0:
        raise ValueError("start must be non-negative")

    end = start + len(expected)
    if end > len(phones):
        raise ValueError(
            f"Expected span {start}:{end} exceeds phone count {len(phones)}"
        )

    observed = phones[start:end]
    if observed != expected:
        raise ValueError(
            f"Full-word guard failed at {start}:{end}; "
            f"expected={expected}, observed={observed}"
        )

    original_span_durations = durations[start:end]
    original_total = sum(original_span_durations)

    if replacement_durations is None:
        replacement_durations = distribute_duration(
            original_total,
            replacement,
            duration_weights,
            minimum_duration,
        )
    else:
        if len(replacement_durations) != len(replacement):
            raise ValueError(
                "Replacement phone/duration count mismatch: "
                f"{len(replacement)} != {len(replacement_durations)}"
            )
        if any(value <= 0 for value in replacement_durations):
            raise ValueError("Replacement durations must all be positive")
        supplied_total = sum(replacement_durations)
        if abs(supplied_total - original_total) > 1e-6:
            raise ValueError(
                "Replacement durations must preserve the complete word span: "
                f"original={original_total:.9f}, replacement={supplied_total:.9f}"
            )

    result = dict(payload)
    new_phones = phones[:start] + replacement + phones[end:]
    new_durations = durations[:start] + replacement_durations + durations[end:]
    result["ph_seq"] = " ".join(new_phones)
    result["ph_dur"] = " ".join(f"{value:.6f}" for value in new_durations)
    if replacement_text is not None:
        result["text"] = replacement_text

    original_full_total = sum(durations)
    replacement_full_total = sum(new_durations)
    if abs(original_full_total - replacement_full_total) > 1e-6:
        raise RuntimeError(
            "Internal invariant failed: full DS duration changed: "
            f"{original_full_total:.9f} != {replacement_full_total:.9f}"
        )

    immutable_keys = [
        "f0_seq",
        "note_seq",
        "note_dur",
        "note_slur",
        "gender",
        "velocity",
        "energy",
        "breathiness",
        "tension",
        "voicing",
    ]
    changed_conditioning = [
        key for key in immutable_keys if result.get(key) != payload.get(key)
    ]
    if changed_conditioning:
        raise RuntimeError(
            f"Conditioning invariants changed unexpectedly: {changed_conditioning}"
        )

    report = {
        "status": "FULL_WORD_REPLACEMENT_READY",
        "replaced_indices": [start, end],
        "original_phones": expected,
        "replacement_phones": replacement,
        "original_durations": original_span_durations,
        "replacement_durations": replacement_durations,
        "original_word_total_sec": original_total,
        "replacement_word_total_sec": sum(replacement_durations),
        "source_phone_count": len(phones),
        "output_phone_count": len(new_phones),
        "full_duration_before_sec": original_full_total,
        "full_duration_after_sec": replacement_full_total,
        "conditioning_unchanged": not changed_conditioning,
        "f0_sha256": sha256_text(str(payload.get("f0_seq", ""))),
    }
    return result, report


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Strictly replace one complete phoneme span in a DiffSinger DS file "
            "while preserving the span duration and acoustic conditioning."
        )
    )
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--start", required=True, type=int)
    parser.add_argument("--expect", required=True, type=parse_phone_sequence)
    parser.add_argument("--replace", required=True, type=parse_phone_sequence)
    parser.add_argument("--durations", type=parse_float_sequence)
    parser.add_argument("--weights", type=parse_float_sequence)
    parser.add_argument("--minimum-duration", type=float, default=DEFAULT_MIN_DURATION)
    parser.add_argument("--text", default=None)
    parser.add_argument("--report", type=Path, default=None)
    args = parser.parse_args()

    if args.durations is not None and args.weights is not None:
        parser.error("Use either --durations or --weights, not both")

    payload, was_list = load_ds(args.input.resolve())
    result, report = replace_word(
        payload=payload,
        start=args.start,
        expected=args.expect,
        replacement=args.replace,
        replacement_durations=args.durations,
        duration_weights=args.weights,
        minimum_duration=args.minimum_duration,
        replacement_text=args.text,
    )

    output = args.output.resolve()
    dump_ds(output, result, was_list)
    report["input"] = str(args.input.resolve())
    report["output"] = str(output)

    if args.report is not None:
        report_path = args.report.resolve()
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(
            json.dumps(report, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )

    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
