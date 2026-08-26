from __future__ import annotations

import argparse
import csv
import json
import shutil
from pathlib import Path

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
    rows = list(csv.DictReader(src_csv.open('r', encoding='utf-8-sig', newline='')))
    if len(rows) != report['segment_count']:
        raise RuntimeError('transcriptions.csv count does not match Stage4 report.')

    durations_report = []
    for row in rows:
        phones = [x for x in row['ph_seq'].split() if x]
        durs = [float(x) for x in row['ph_dur'].split() if x]
        if len(phones) != len(durs):
            raise RuntimeError(f"Phone/duration mismatch: {row['name']}: {len(phones)} != {len(durs)}")
        if not phones or any(d <= 0 for d in durs):
            raise RuntimeError(f"Invalid phone durations: {row['name']}")
        src = src_wavs / f"{row['name']}.wav"
        if not src.exists():
            raise FileNotFoundError(src)
        info = sf.info(str(src))
        audio_duration = float(info.frames / info.samplerate)
        phone_duration = float(sum(durs))
        error = abs(audio_duration - phone_duration)
        # The CTC alignment can leave a small tail/head uncovered. Keep it within 250 ms.
        if error > 0.25:
            raise RuntimeError(
                f"Duration coverage too far from audio for {row['name']}: "
                f"audio={audio_duration:.3f}s phones={phone_duration:.3f}s error={error:.3f}s"
            )
        shutil.copy2(src, wavs / src.name)
        durations_report.append({
            'name': row['name'],
            'sample_rate': int(info.samplerate),
            'channels': int(info.channels),
            'audio_duration': audio_duration,
            'phone_duration': phone_duration,
            'coverage_error': error,
        })

    dst_csv = raw / 'transcriptions.csv'
    with dst_csv.open('w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['name', 'ph_seq', 'ph_dur'])
        writer.writeheader()
        writer.writerows(rows)

    shutil.copy2(stage4 / 'phonemes.txt', output / 'phonemes.txt')
    shutil.copy2(stage4 / 'phone_set.json', output / 'phone_set.json')

    max_error = max(x['coverage_error'] for x in durations_report)
    result = {
        'schema_version': '0.4',
        'status': 'RAW_DATASET_VALIDATED',
        'segment_count': len(rows),
        'wav_count': len(list(wavs.glob('*.wav'))),
        'phone_csv': str(dst_csv),
        'phonemes': str(output / 'phonemes.txt'),
        'max_duration_coverage_error_sec': max_error,
        'segments': durations_report,
        'training_allowed': False,
        'next_gate': 'DIFFSINGER_BINARIZE_CONFIG_AND_PREPROCESS',
        'note': 'This is a raw dataset bake/validation. It intentionally does not invoke the DiffSinger binarizer until the project-local acoustic configuration is validated for the custom Arabic phone-set.',
    }
    (output / 'dataset_stage5.json').write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps({k: result[k] for k in ('status','segment_count','wav_count','max_duration_coverage_error_sec','training_allowed','next_gate')}, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
