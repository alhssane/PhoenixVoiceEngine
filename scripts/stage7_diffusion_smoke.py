from __future__ import annotations

import argparse
import json
import pickle
from pathlib import Path


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument('--diffsinger', required=True)
    ap.add_argument('--config', required=True)
    ap.add_argument('--binary', required=True)
    args = ap.parse_args()

    ds = Path(args.diffsinger).resolve()
    config = Path(args.config).resolve()
    binary = Path(args.binary).resolve()
    python = Path(r'D:\PhoenixVoiceEngine\.venv_phoenix_svs\Scripts\python.exe')

    if not python.exists():
        raise FileNotFoundError(f'SVS Python not found: {python}')
    if not config.exists():
        raise FileNotFoundError(f'Config not found: {config}')
    if not binary.exists():
        raise FileNotFoundError(f'Binary dataset not found: {binary}')
    if not (ds / 'scripts' / 'train.py').exists():
        raise FileNotFoundError(f'DiffSinger train.py not found: {ds / "scripts" / "train.py"}')

    required = [
        binary / 'train.data', binary / 'train.meta',
        binary / 'valid.data', binary / 'valid.meta',
        binary / 'spk_map.json', binary / 'lang_map.json',
        binary / 'dictionary-ar.txt', binary / 'phoneme_distribution.jpg',
    ]
    missing = [str(p) for p in required if not p.exists()]
    if missing:
        raise FileNotFoundError('Missing binary artifacts:\n' + '\n'.join(missing))

    with (binary / 'train.meta').open('rb') as f:
        train_meta = pickle.load(f)
    with (binary / 'valid.meta').open('rb') as f:
        valid_meta = pickle.load(f)

    train_count = len(train_meta['lengths'])
    valid_count = len(valid_meta['lengths'])
    if train_count <= 0 or valid_count <= 0:
        raise RuntimeError(f'Invalid split sizes: train={train_count}, valid={valid_count}')

    # Use the same IndexedDataset format as OpenVPI DiffSinger to validate
    # that every stored item contains the core acoustic training tensors.
    import h5py

    expected = {'tokens', 'mel2ph', 'mel', 'f0'}
    stats = {}
    for prefix, count in (('train', train_count), ('valid', valid_count)):
        path = binary / f'{prefix}.data'
        with h5py.File(path, 'r') as h5:
            if len(h5) != count:
                raise RuntimeError(f'{prefix}.data count {len(h5)} != meta count {count}')
            token_min = None
            token_max = None
            mel_lengths = []
            for i in range(count):
                grp = h5[str(i)]
                keys = set(grp.keys())
                missing_keys = expected - keys
                if missing_keys:
                    raise RuntimeError(f'{prefix}[{i}] missing fields: {sorted(missing_keys)}')
                tokens = grp['tokens'][()]
                mel2ph = grp['mel2ph'][()]
                mel = grp['mel'][()]
                f0 = grp['f0'][()]
                if len(tokens) == 0 or len(mel) == 0 or len(f0) == 0 or len(mel2ph) == 0:
                    raise RuntimeError(f'{prefix}[{i}] contains an empty core tensor')
                if mel.shape[0] != mel2ph.shape[0] or f0.shape[0] != mel2ph.shape[0]:
                    raise RuntimeError(
                        f'{prefix}[{i}] frame mismatch: mel={mel.shape[0]} mel2ph={mel2ph.shape[0]} f0={f0.shape[0]}'
                    )
                tmin = int(tokens.min())
                tmax = int(tokens.max())
                token_min = tmin if token_min is None else min(token_min, tmin)
                token_max = tmax if token_max is None else max(token_max, tmax)
                mel_lengths.append(int(mel.shape[0]))
        stats[prefix] = {
            'items': count,
            'token_min': token_min,
            'token_max': token_max,
            'mel_frames_min': min(mel_lengths),
            'mel_frames_max': max(mel_lengths),
        }

    result = {
        'status': 'STAGE7_BINARY_INTEGRITY_OK',
        'train_items': train_count,
        'valid_items': valid_count,
        'train': stats['train'],
        'valid': stats['valid'],
        'next_gate': 'DIFFSINGER_TWO_STEP_TRAIN_SMOKE',
        'training_allowed': False,
    }
    (binary / 'stage7_preflight_report.json').write_text(
        json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8'
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
