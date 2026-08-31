from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from statistics import median


def main() -> int:
    ap = argparse.ArgumentParser(description='Audit training phone-duration patterns for a contiguous phoneme sequence.')
    ap.add_argument('--root', required=True, help='Phoenix training job root containing transcriptions.csv files.')
    ap.add_argument('--phones', nargs='+', required=True)
    ap.add_argument('--output', required=True)
    args = ap.parse_args()

    root = Path(args.root).resolve()
    target = list(args.phones)
    rows_out = []

    for csv_path in root.rglob('transcriptions.csv'):
        try:
            rows = list(csv.DictReader(csv_path.open('r', encoding='utf-8-sig')))
        except Exception:
            continue
        for row in rows:
            seq = str(row.get('ph_seq', '')).split()
            dur_raw = str(row.get('ph_dur', '')).split()
            if len(seq) != len(dur_raw):
                continue
            try:
                dur = [float(x) for x in dur_raw]
            except ValueError:
                continue
            for i in range(0, len(seq) - len(target) + 1):
                if seq[i:i + len(target)] == target:
                    vals = dur[i:i + len(target)]
                    total = sum(vals)
                    rows_out.append({
                        'csv': str(csv_path),
                        'name': row.get('name', ''),
                        'index': i,
                        'phones': target,
                        'durations_sec': vals,
                        'total_sec': total,
                        'ratios': [v / total if total else 0.0 for v in vals],
                    })

    if not rows_out:
        raise RuntimeError(f'No contiguous training occurrence found for: {target}')

    med = [median(x['durations_sec'][j] for x in rows_out) for j in range(len(target))]
    med_total = sum(med)
    median_ratios = [x / med_total if med_total else 0.0 for x in med]

    result = {
        'status': 'TRAINING_PHONE_DURATION_PATTERN_AUDIT_V1',
        'target_phones': target,
        'occurrence_count': len(rows_out),
        'median_duration_sec': med,
        'median_duration_ratios': median_ratios,
        'min_duration_sec': [min(x['durations_sec'][j] for x in rows_out) for j in range(len(target))],
        'max_duration_sec': [max(x['durations_sec'][j] for x in rows_out) for j in range(len(target))],
        'occurrences': rows_out,
    }

    out = Path(args.output).resolve()
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
