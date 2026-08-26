from __future__ import annotations

import argparse
import json
from pathlib import Path


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument('--project', default=r'D:\PhoenixVoiceEngine')
    args = ap.parse_args()
    root = Path(args.project).resolve()
    ds = root / 'external' / 'DiffSinger-openvpi'
    candidates = []
    roots = [
        ds / 'checkpoints',
        root / 'checkpoints',
        root / 'models',
    ]
    seen = set()
    for base in roots:
        if not base.exists():
            continue
        for p in base.rglob('*'):
            if not p.is_file() or p.suffix.lower() not in {'.ckpt', '.pt', '.pth'}:
                continue
            s = str(p.resolve())
            if s in seen:
                continue
            seen.add(s)
            candidates.append({
                'path': s,
                'size_mb': round(p.stat().st_size / 1024**2, 2),
                'name': p.name,
            })
    candidates.sort(key=lambda x: x['size_mb'], reverse=True)
    result = {
        'status': 'STAGE8_CHECKPOINT_AUDIT',
        'diffsinger_version_hint': 'OpenVPI 2.5.x',
        'target_arch': {
            'vocab_size': 29,
            'hidden_size': 256,
            'audio_sample_rate': 44100,
            'mel_bins': 128,
            'hop_size': 512,
            'diffusion_type': 'reflow',
            'backbone_type': 'lynxnet',
        },
        'candidates': candidates,
        'candidate_count': len(candidates),
        'next_gate': 'CHECKPOINT_COMPATIBILITY',
        'training_allowed': False,
    }
    out = root / 'reports'
    out.mkdir(parents=True, exist_ok=True)
    (out / 'stage8_checkpoint_audit.json').write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
