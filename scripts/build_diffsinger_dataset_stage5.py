from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

import numpy as np
import soundfile as sf


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument('--stage4', required=True)
    ap.add_argument('--output', required=True)
    args = ap.parse_args()

    stage4 = Path(args.stage4).resolve()
    output = Path(args.output).resolve()
    raw = output / 'raw'
    wavs = raw / 'wavs'
    wavs.mkdir(parents=True, exist_ok=True)

    report = json.loads((stage4 / 'dataset_stage4_ar.json').read_text(encoding='utf-8'))
    if report.get('status') != 'ARABIC_PHONESET_READY' or report.get('segment_count') != 11:
        raise RuntimeError('Stage4 Arabic phone-set dataset is not ready for bake.')

    src_csv = stage4 / 'raw' / 'transcriptions.csv'
    src_wavs = stage4 / 'raw' / 'wavs'
    stage3 = stage4.parent / 'freed_joud_diffsinger_stage3'
    phones_dir = stage3 / 'phones'
    if not phones_dir.exists():
        raise FileNotFoundError(f'Missing Stage3 phone alignments: {phones_dir}')

    rows = list(csv.DictReader(src_csv.open('r', encoding='utf-8-sig', newline='')))
    if len(rows) != report['segment_count']:
        raise RuntimeError('transcriptions.csv count does not match Stage4 report.')

    durations_report = []
    baked_rows = []

    for row in rows:
        name = row['name']
        phones = [x for x in row['ph_seq'].split() if x]
        durs = [float(x) for x in row['ph_dur'].split() if x]
        if len(phones) != len(durs):
            raise RuntimeError(f"Phone/duration mismatch: {name}: {len(phones)} != {len(durs)}")
        if not phones or any(d <= 0 for d in durs):
            raise RuntimeError(f"Invalid phone durations: {name}")

        src = src_wavs / f'{name}.wav'
        alignment_path = phones_dir / f'{name}.json'
        if not src.exists():
            raise FileNotFoundError(src)
        if not alignment_path.exists():
            raise FileNotFoundError(alignment_path)

        payload = json.loads(alignment_path.read_text(encoding='utf-8'))
        aligned = [x for x in payload.get('alignment', []) if x.get('aligned') and float(x.get('duration', 0.0)) > 0]
        if not aligned:
            raise RuntimeError(f'No aligned phone span available for {name}')

        # Stage3 durations represent the contiguous aligned speech span.
        # Trim the Stage4 source WAV to exactly that span rather than forcing
        # silence/music tails into phoneme durations.
        start_s = max(0.0, float(min(x['start'] for x in aligned)))
        end_s = float(max(x['end'] for x in aligned))
        if end_s <= start_s:
            raise RuntimeError(f'Invalid aligned span for {name}: {start_s}..{end_s}')

        audio, sr = sf.read(str(src), dtype='float32', always_2d=False)
        if audio.ndim == 1:
            channels = 1
            total_frames = len(audio)
        else:
            channels = int(audio.shape[1])
            total_frames = int(audio.shape[0])

        start_frame = max(0, min(total_frames - 1, int(round(start_s * sr))))
        end_frame = max(start_frame + 1, min(total_frames, int(round(end_s * sr))))
        trimmed = audio[start_frame:end_frame]
        baked_duration = float(trimmed.shape[0] / sr)
        phone_duration = float(sum(durs))
        error = abs(baked_duration - phone_duration)

        # Allow a small frame-quantization difference after trimming.
        if error > 0.05:
            raise RuntimeError(
                f"Duration coverage mismatch after alignment trim for {name}: "
                f"audio={baked_duration:.4f}s phones={phone_duration:.4f}s error={error:.4f}s "
                f"span={start_s:.4f}-{end_s:.4f}s"
            )

        dst = wavs / src.name
        sf.write(str(dst), trimmed, sr, subtype='PCM_16')

        baked_rows.append(row)
        durations_report.append({
            'name': name,
            'sample_rate': int(sr),
            'channels': channels,
            'source_duration': float(total_frames / sr),
            'trim_start_sec': start_s,
            'trim_end_sec': end_s,
            'baked_duration': baked_duration,
            'phone_duration': phone_duration,
            'coverage_error': error,
        })

    dst_csv = raw / 'transcriptions.csv'
    with dst_csv.open('w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['name', 'ph_seq', 'ph_dur'])
        writer.writeheader()
        writer.writerows(baked_rows)

    (output / 'phonemes.txt').write_text((stage4 / 'phonemes.txt').read_text(encoding='utf-8'), encoding='utf-8')
    (output / 'phone_set.json').write_text((stage4 / 'phone_set.json').read_text(encoding='utf-8'), encoding='utf-8')

    max_error = max(x['coverage_error'] for x in durations_report)
    result = {
        'schema_version': '0.5',
        'status': 'RAW_DATASET_VALIDATED',
        'segment_count': len(baked_rows),
        'wav_count': len(list(wavs.glob('*.wav'))),
        'phone_csv': str(dst_csv),
        'phonemes': str(output / 'phonemes.txt'),
        'max_duration_coverage_error_sec': max_error,
        'segments': durations_report,
        'training_allowed': False,
        'next_gate': 'DIFFSINGER_BINARIZE_CONFIG_AND_PREPROCESS',
        'note': 'Raw dataset is trimmed to the Stage3 aligned speech span so phoneme durations cover the baked audio without importing unrelated silence/music tails.',
    }
    (output / 'dataset_stage5.json').write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps({k: result[k] for k in ('status','segment_count','wav_count','max_duration_coverage_error_sec','training_allowed','next_gate')}, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
