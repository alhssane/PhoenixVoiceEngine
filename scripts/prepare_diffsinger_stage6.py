from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path


def read_csv(path: Path):
    with path.open('r', encoding='utf-8-sig', newline='') as f:
        return list(csv.DictReader(f))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument('--raw', required=True)
    ap.add_argument('--diffsinger', required=True)
    ap.add_argument('--config', required=True)
    ap.add_argument('--binary', required=True)
    args = ap.parse_args()

    raw = Path(args.raw).resolve()
    ds = Path(args.diffsinger).resolve()
    config = Path(args.config).resolve()
    binary = Path(args.binary).resolve()

    csv_path = raw / 'raw' / 'transcriptions.csv'
    wavs = raw / 'raw' / 'wavs'
    phones_path = raw / 'phonemes.txt'
    report_path = raw / 'dataset_stage5.json'

    for p in (csv_path, wavs, phones_path, report_path):
        if not p.exists():
            raise FileNotFoundError(f'Missing required Stage5 artifact: {p}')
    if not (ds / 'configs' / 'acoustic.yaml').exists():
        raise FileNotFoundError(f'DiffSinger acoustic config not found: {ds / "configs" / "acoustic.yaml"}')

    report = json.loads(report_path.read_text(encoding='utf-8'))
    if report.get('status') != 'RAW_DATASET_VALIDATED':
        raise RuntimeError('Stage5 report is not RAW_DATASET_VALIDATED.')
    if report.get('segment_count') != report.get('wav_count'):
        raise RuntimeError('Stage5 segment/wav counts do not match.')

    rows = read_csv(csv_path)
    if len(rows) != report.get('segment_count'):
        raise RuntimeError('transcriptions.csv count does not match Stage5 report.')

    phones = [p.strip() for p in phones_path.read_text(encoding='utf-8').splitlines() if p.strip()]
    if not phones:
        raise RuntimeError('phonemes.txt is empty.')
    special = {'SP', 'AP', '<PAD>'}
    extra = [p for p in phones if p not in special]

    for row in rows:
        name = row['name']
        seq = row['ph_seq'].split()
        dur = row['ph_dur'].split()
        if len(seq) != len(dur):
            raise RuntimeError(f'Phone/duration mismatch in {name}.')
        wav = wavs / f'{name}.wav'
        if not wav.exists():
            raise FileNotFoundError(f'Missing WAV: {wav}')
        bad = [p for p in seq if p not in phones]
        if bad:
            raise RuntimeError(f'Unsupported phones in {name}: {sorted(set(bad))}')

    test_prefixes = [r['name'] for r in rows[-2:]] if len(rows) >= 3 else [rows[-1]['name']]
    raw_posix = raw.as_posix()
    binary_posix = binary.as_posix()

    dictionary = config.parent / 'phoenix_arabic_dictionary.txt'
    dictionary.parent.mkdir(parents=True, exist_ok=True)
    # DiffSinger requires a dictionary file for every declared language. The
    # acoustic transcriptions already contain phoneme sequences directly; this
    # compact entry registers the complete Arabic phone inventory for language
    # `ar` without introducing a word-level lexicon that could alter ph_seq.
    dictionary_line = 'PHOENIX_ARABIC\t' + ' '.join(extra)
    dictionary.write_text(dictionary_line + '\n', encoding='utf-8')

    lines = [
        'base_config:',
        '  - configs/acoustic.yaml',
        '',
        'dictionaries:',
        '  ar: ' + dictionary.as_posix(),
        'extra_phonemes:',
        *[f'  - {p}' for p in extra],
        'merged_phoneme_groups: []',
        '',
        'datasets:',
        '  - raw_data_dir: ' + raw_posix,
        '    speaker: freed_joud',
        '    spk_id: 0',
        '    language: ar',
        '    test_prefixes:',
        *[f'      - {x}' for x in test_prefixes],
        '',
        'binary_data_dir: ' + binary_posix,
        'binarization_args:',
        '  shuffle: false',
        '  num_workers: 0',
        'use_lang_id: false',
        'num_lang: 1',
        'use_spk_id: false',
        'num_spk: 1',
        'val_with_vocoder: false',
        'hnsep: null',
        'hnsep_ckpt: null',
        'use_key_shift_embed: false',
        'use_speed_embed: false',
        '',
    ]
    config.parent.mkdir(parents=True, exist_ok=True)
    config.write_text('\n'.join(lines), encoding='utf-8')

    result = {
        'status': 'STAGE6_CONFIG_READY',
        'segments': len(rows),
        'phoneme_count': len(phones),
        'extra_phoneme_count': len(extra),
        'dictionary_language': 'ar',
        'dictionary': str(dictionary),
        'config': str(config),
        'binary_data_dir': str(binary),
        'diffsinger': str(ds),
        'training_allowed': False,
        'next_gate': 'DIFFSINGER_BINARIZE',
    }
    (config.parent / 'stage6_config_report.json').write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
