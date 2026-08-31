from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import statistics
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def parse_float_sequence(value: str) -> list[float]:
    return [float(x) for x in str(value).split() if str(x).strip()]


def percentile(values: list[float], q: float) -> float | None:
    if not values:
        return None
    xs = sorted(values)
    if len(xs) == 1:
        return xs[0]
    pos = (len(xs) - 1) * q
    lo = math.floor(pos)
    hi = math.ceil(pos)
    if lo == hi:
        return xs[lo]
    return xs[lo] * (hi - pos) + xs[hi] * (pos - lo)


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Audit final Stage5 phoneme alignment quality without modifying data."
    )
    ap.add_argument("--csv", type=Path, required=True, help="Final Stage5 transcriptions.csv")
    ap.add_argument("--output-json", type=Path, required=True)
    ap.add_argument("--output-csv", type=Path, required=True)
    ap.add_argument("--short-threshold", type=float, default=0.03)
    ap.add_argument("--long-threshold", type=float, default=0.40)
    ap.add_argument("--context-min-count", type=int, default=2)
    args = ap.parse_args()

    source = args.csv.resolve()
    if not source.is_file():
        raise FileNotFoundError(source)

    with source.open("r", encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))

    if not rows:
        raise RuntimeError("Stage5 CSV is empty.")

    anomalies: list[dict[str, Any]] = []
    phone_durations: dict[str, list[float]] = defaultdict(list)
    trigram_occurrences: dict[tuple[str, str, str], list[dict[str, Any]]] = defaultdict(list)
    exact_record_keys: Counter[str] = Counter()
    names: Counter[str] = Counter()
    total_phones = 0
    total_duration = 0.0
    invalid_rows = 0

    for row_index, row in enumerate(rows):
        name = str(row.get("name") or row.get("item_name") or row.get("wav_fn") or f"row_{row_index}")
        names[name] += 1
        ph_seq = str(row.get("ph_seq", "")).strip()
        ph_dur = str(row.get("ph_dur", "")).strip()
        text = str(row.get("txt") or row.get("text") or "")

        phones = ph_seq.split()
        try:
            durations = parse_float_sequence(ph_dur)
        except ValueError:
            invalid_rows += 1
            anomalies.append({
                "severity": "critical",
                "type": "NON_NUMERIC_DURATION",
                "row_index": row_index,
                "name": name,
                "ph_dur": ph_dur,
            })
            continue

        exact_record_keys[sha256_text(ph_seq + "\n" + ph_dur + "\n" + text)] += 1

        if len(phones) != len(durations):
            invalid_rows += 1
            anomalies.append({
                "severity": "critical",
                "type": "PHONE_DURATION_LENGTH_MISMATCH",
                "row_index": row_index,
                "name": name,
                "phone_count": len(phones),
                "duration_count": len(durations),
            })
            continue

        if not phones:
            invalid_rows += 1
            anomalies.append({
                "severity": "critical",
                "type": "EMPTY_PHONE_SEQUENCE",
                "row_index": row_index,
                "name": name,
            })
            continue

        total_phones += len(phones)
        total_duration += sum(durations)

        for i, (phone, dur) in enumerate(zip(phones, durations)):
            phone_durations[phone].append(dur)
            left = phones[i - 1] if i > 0 else "<BOS>"
            right = phones[i + 1] if i + 1 < len(phones) else "<EOS>"

            if dur <= 0:
                anomalies.append({
                    "severity": "critical",
                    "type": "NON_POSITIVE_DURATION",
                    "row_index": row_index,
                    "name": name,
                    "phone_index": i,
                    "phone": phone,
                    "duration_sec": dur,
                    "context": [left, phone, right],
                })
            elif dur < args.short_threshold:
                anomalies.append({
                    "severity": "warning",
                    "type": "VERY_SHORT_PHONE",
                    "row_index": row_index,
                    "name": name,
                    "phone_index": i,
                    "phone": phone,
                    "duration_sec": dur,
                    "context": [left, phone, right],
                })
            elif dur > args.long_threshold:
                anomalies.append({
                    "severity": "warning",
                    "type": "VERY_LONG_PHONE",
                    "row_index": row_index,
                    "name": name,
                    "phone_index": i,
                    "phone": phone,
                    "duration_sec": dur,
                    "context": [left, phone, right],
                })

        for i in range(len(phones) - 2):
            tri = tuple(phones[i : i + 3])
            tri_durs = durations[i : i + 3]
            trigram_occurrences[tri].append({
                "name": name,
                "row_index": row_index,
                "phone_index": i,
                "durations_sec": tri_durs,
                "total_sec": sum(tri_durs),
            })

    phone_stats: dict[str, Any] = {}
    for phone, values in sorted(phone_durations.items()):
        med = statistics.median(values)
        mad = statistics.median([abs(v - med) for v in values]) if values else 0.0
        phone_stats[phone] = {
            "count": len(values),
            "min": min(values),
            "p10": percentile(values, 0.10),
            "median": med,
            "p90": percentile(values, 0.90),
            "max": max(values),
            "mean": statistics.fmean(values),
            "mad": mad,
        }

    context_stats: list[dict[str, Any]] = []
    for tri, occs in trigram_occurrences.items():
        if len(occs) < args.context_min_count:
            continue
        per_pos = [[float(o["durations_sec"][j]) for o in occs] for j in range(3)]
        medians = [statistics.median(v) for v in per_pos]
        mins = [min(v) for v in per_pos]
        maxs = [max(v) for v in per_pos]
        ratios = [maxs[i] / max(mins[i], 1e-8) for i in range(3)]
        totals = [float(o["total_sec"]) for o in occs]
        context_stats.append({
            "phones": list(tri),
            "count": len(occs),
            "median_duration_sec": medians,
            "min_duration_sec": mins,
            "max_duration_sec": maxs,
            "max_min_ratio": ratios,
            "total_min_sec": min(totals),
            "total_median_sec": statistics.median(totals),
            "total_max_sec": max(totals),
            "occurrences": occs,
        })

    context_stats.sort(
        key=lambda x: (max(x["max_min_ratio"]), x["count"]), reverse=True
    )

    duplicate_record_groups = sum(1 for c in exact_record_keys.values() if c > 1)
    duplicate_rows = sum(c - 1 for c in exact_record_keys.values() if c > 1)
    duplicate_name_groups = sum(1 for c in names.values() if c > 1)

    severity_counts = Counter(a["severity"] for a in anomalies)
    type_counts = Counter(a["type"] for a in anomalies)

    result = {
        "status": "STAGE5_ALIGNMENT_QUALITY_AUDIT_V1",
        "source_csv": str(source),
        "scope": "FINAL_STAGE5_ONLY",
        "thresholds": {
            "very_short_phone_sec": args.short_threshold,
            "very_long_phone_sec": args.long_threshold,
            "context_min_count": args.context_min_count,
        },
        "dataset_summary": {
            "row_count": len(rows),
            "invalid_row_count": invalid_rows,
            "unique_name_count": len(names),
            "duplicate_name_group_count": duplicate_name_groups,
            "exact_duplicate_record_group_count": duplicate_record_groups,
            "exact_duplicate_extra_row_count": duplicate_rows,
            "total_phone_count": total_phones,
            "total_duration_sec": total_duration,
            "unique_phone_count": len(phone_durations),
            "repeated_trigram_count": len(context_stats),
        },
        "anomaly_summary": {
            "severity_counts": dict(severity_counts),
            "type_counts": dict(type_counts),
            "total": len(anomalies),
        },
        "phone_duration_stats": phone_stats,
        "most_inconsistent_repeated_contexts": context_stats[:100],
        "anomalies": anomalies,
        "interpretation_rules": {
            "critical": "Rows with invalid or unusable phone-duration data.",
            "warning": "Durations outside configured plausibility thresholds; requires audio/alignment review, not automatic deletion.",
            "context_variance": "Large max/min ratios for the same trigram indicate inconsistent alignment or genuinely different singing articulation; inspect the referenced rows before deciding.",
        },
    }

    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(
        json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    args.output_csv.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "severity",
        "type",
        "row_index",
        "name",
        "phone_index",
        "phone",
        "duration_sec",
        "context",
        "phone_count",
        "duration_count",
    ]
    with args.output_csv.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for item in anomalies:
            row = dict(item)
            if isinstance(row.get("context"), list):
                row["context"] = " ".join(row["context"])
            writer.writerow(row)

    print(json.dumps({
        "status": result["status"],
        "source_csv": str(source),
        "output_json": str(args.output_json.resolve()),
        "output_csv": str(args.output_csv.resolve()),
        "dataset_summary": result["dataset_summary"],
        "anomaly_summary": result["anomaly_summary"],
        "top_inconsistent_contexts": [
            {
                "phones": x["phones"],
                "count": x["count"],
                "max_min_ratio": x["max_min_ratio"],
            }
            for x in context_stats[:10]
        ],
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
