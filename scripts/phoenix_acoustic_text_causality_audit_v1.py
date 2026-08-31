from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from pathlib import Path
from typing import Any

import numpy as np
import torch


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def set_seed(seed: int) -> None:
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)


def clone_param_with_replacement(param: dict[str, Any], start: int, expect: list[str], replace: list[str]) -> dict[str, Any]:
    phones = str(param['ph_seq']).split()
    end = start + len(expect)
    observed = phones[start:end]
    if observed != expect:
        raise RuntimeError(f'Reference guard failed at {start}:{end}: expected {expect}, observed {observed}.')
    if len(replace) != len(expect):
        raise RuntimeError('This audit requires equal-length phone replacement so the timing map stays identical.')
    out = dict(param)
    new_phones = list(phones)
    new_phones[start:end] = replace
    out['ph_seq'] = ' '.join(new_phones)
    return out


def rel_l2(a: torch.Tensor, b: torch.Tensor, mask: torch.Tensor | None = None) -> float:
    x = a.detach().float()
    y = b.detach().float()
    if mask is not None:
        x = x[mask]
        y = y[mask]
    denom = max(float(x.norm().cpu()), 1e-8)
    return float((x - y).norm().cpu()) / denom


def cosine_distance(a: torch.Tensor, b: torch.Tensor, mask: torch.Tensor | None = None) -> float:
    x = a.detach().float()
    y = b.detach().float()
    if mask is not None:
        x = x[mask]
        y = y[mask]
    x = x.reshape(-1)
    y = y.reshape(-1)
    denom = max(float(x.norm().cpu() * y.norm().cpu()), 1e-8)
    return 1.0 - float(torch.dot(x, y).cpu()) / denom


def main() -> int:
    ap = argparse.ArgumentParser(description='Phoenix DiffSinger acoustic text-causality audit.')
    ap.add_argument('--diffsinger-root', required=True)
    ap.add_argument('--exp', required=True)
    ap.add_argument('--ckpt', type=int, required=True)
    ap.add_argument('--checkpoint-file', type=Path, required=True)
    ap.add_argument('--control-ds', type=Path, required=True)
    ap.add_argument('--output', type=Path, required=True)
    ap.add_argument('--start-phone', type=int, default=11)
    ap.add_argument('--expect', nargs='+', default=['n', 'f', 'i'])
    ap.add_argument('--replace', nargs='+', default=['b', 'a', 'b'])
    ap.add_argument('--seed', type=int, default=20260831)
    ap.add_argument('--with-vocoder', action='store_true', help='Run final waveform inference too; internal mel audit is always performed.')
    args = ap.parse_args()

    root = Path(args.diffsinger_root).resolve()
    control_path = args.control_ds.resolve()
    checkpoint_file = args.checkpoint_file.resolve()
    output = args.output.resolve()
    if not root.is_dir():
        raise FileNotFoundError(root)
    if not control_path.is_file():
        raise FileNotFoundError(control_path)
    if not checkpoint_file.is_file():
        raise FileNotFoundError(checkpoint_file)

    os.environ['PYTHONPATH'] = str(root)
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))

    payload = json.loads(control_path.read_text(encoding='utf-8-sig'))
    if not isinstance(payload, list) or len(payload) != 1:
        raise RuntimeError('Audit expects a one-segment DS file.')
    control_param = payload[0]
    for key in ('ph_seq', 'ph_dur', 'f0_seq', 'f0_timestep'):
        if key not in control_param:
            raise RuntimeError(f'Control DS missing required field: {key}')

    mutant_param = clone_param_with_replacement(control_param, args.start_phone, args.expect, args.replace)

    old_cwd = Path.cwd()
    old_argv = sys.argv[:]
    try:
        os.chdir(root)
        sys.argv = ['phoenix_acoustic_text_causality_audit_v1.py', '--exp_name', args.exp, '--infer']
        from utils.hparams import set_hparams, hparams
        set_hparams(print_hparams=False)

        from inference.ds_acoustic import DiffSingerAcousticInfer

        infer = DiffSingerAcousticInfer(load_vocoder=args.with_vocoder, ckpt_steps=args.ckpt)

        def prepare(param: dict[str, Any], idx: int = 0) -> dict[str, torch.Tensor]:
            p = dict(param)
            p.setdefault('lang', 'ar')
            return infer.preprocess_input(p, idx=idx)

        control_batch = prepare(control_param, 0)
        mutant_batch = prepare(mutant_param, 0)

        if tuple(control_batch['mel2ph'].shape) != tuple(mutant_batch['mel2ph'].shape):
            raise RuntimeError('Control and mutant produced different mel2ph shapes; equal-length phone mutation invariant failed.')

        mel2ph = control_batch['mel2ph'][0]
        phone_start = args.start_phone + 1
        phone_end = args.start_phone + len(args.expect)
        local_mask = (mel2ph >= phone_start) & (mel2ph <= phone_end)

        # The two DS files intentionally share the same durations and F0. This audit
        # checks the resulting internal representations, without changing weights.
        with torch.no_grad():
            c_tokens = control_batch['tokens']
            m_tokens = mutant_batch['tokens']
            c_txt = infer.model.fs2.txt_embed(c_tokens)
            m_txt = infer.model.fs2.txt_embed(m_tokens)

            c_condition = infer.model.fs2(
                c_tokens, control_batch['mel2ph'], control_batch['f0']
            )
            m_condition = infer.model.fs2(
                m_tokens, mutant_batch['mel2ph'], mutant_batch['f0']
            )

            if not hasattr(infer.model, 'aux_decoder'):
                raise RuntimeError('Loaded acoustic model has no aux_decoder; this audit expects shallow diffusion.')

            set_seed(args.seed)
            c_aux = infer.model.aux_decoder(c_condition, infer=True)
            set_seed(args.seed)
            m_aux = infer.model.aux_decoder(m_condition, infer=True)

            set_seed(args.seed)
            c_diff = infer.model.diffusion(c_condition, src_spec=c_aux, infer=True)
            set_seed(args.seed)
            m_diff = infer.model.diffusion(m_condition, src_spec=m_aux, infer=True)

        result: dict[str, Any] = {
            'status': 'PHOENIX_ACOUSTIC_TEXT_CAUSALITY_AUDIT_V1',
            'project': 'PhoenixVoiceEngine',
            'exp': args.exp,
            'ckpt': args.ckpt,
            'checkpoint_file': str(checkpoint_file),
            'checkpoint_sha256': sha256_file(checkpoint_file),
            'control_ds': str(control_path),
            'mutation': {
                'start_phone': args.start_phone,
                'end_phone_exclusive': args.start_phone + len(args.expect),
                'expect': args.expect,
                'replace': args.replace,
                'changed_field': 'ph_seq',
                'local_frame_count': int(local_mask.sum().item()),
            },
            'config': {
                'audio_sample_rate': hparams.get('audio_sample_rate'),
                'audio_num_mel_bins': hparams.get('audio_num_mel_bins'),
                'hop_size': hparams.get('hop_size'),
                'hidden_size': hparams.get('hidden_size'),
                'use_shallow_diffusion': hparams.get('use_shallow_diffusion'),
                'diffusion_type': hparams.get('diffusion_type'),
                'use_pos_embed': hparams.get('use_pos_embed'),
                'use_lang_id': hparams.get('use_lang_id'),
                'shallow_diffusion_args': hparams.get('shallow_diffusion_args'),
            },
            'shapes': {
                'tokens': list(control_batch['tokens'].shape),
                'mel2ph': list(control_batch['mel2ph'].shape),
                'f0': list(control_batch['f0'].shape),
                'text_embedding': list(c_txt.shape),
                'condition': list(c_condition.shape),
                'aux_mel': list(c_aux.shape),
                'diffusion_mel': list(c_diff.shape),
            },
            'metrics': {
                'text_embedding_local_relative_l2': rel_l2(c_txt, m_txt),
                'text_embedding_global_relative_l2': rel_l2(c_txt, m_txt),
                'fs2_condition_local_relative_l2': rel_l2(c_condition, m_condition, local_mask),
                'fs2_condition_global_relative_l2': rel_l2(c_condition, m_condition),
                'auxiliary_mel_local_relative_l2': rel_l2(c_aux, m_aux, local_mask),
                'auxiliary_mel_global_relative_l2': rel_l2(c_aux, m_aux),
                'auxiliary_mel_local_cosine_distance': cosine_distance(c_aux, m_aux, local_mask),
                'diffusion_mel_local_relative_l2': rel_l2(c_diff, m_diff, local_mask),
                'diffusion_mel_global_relative_l2': rel_l2(c_diff, m_diff),
                'diffusion_mel_local_cosine_distance': cosine_distance(c_diff, m_diff, local_mask),
            },
            'interpretation': {},
        }

        fs2_delta = result['metrics']['fs2_condition_local_relative_l2']
        aux_delta = result['metrics']['auxiliary_mel_local_relative_l2']
        diff_delta = result['metrics']['diffusion_mel_local_relative_l2']

        if aux_delta < max(fs2_delta * 0.25, 1e-4):
            diagnosis = 'TEXT_EFFECT_COLLAPSES_BEFORE_OR_AT_AUX_MEL'
            explanation = 'Phoneme mutation reaches token/text conditioning, but the local auxiliary mel barely changes. Investigate FS2 training, data diversity, alignment, and positional/trajectory shortcuts before retraining diffusion.'
        elif diff_delta < max(aux_delta * 0.25, 1e-4):
            diagnosis = 'TEXT_EFFECT_COLLAPSES_IN_DIFFUSION'
            explanation = 'Auxiliary mel responds materially to the phoneme mutation, but the diffusion output suppresses/reverts most of the local change.'
        else:
            diagnosis = 'TEXT_EFFECT_SURVIVES_TO_FINAL_MEL'
            explanation = 'The phoneme mutation survives through the diffusion mel. If the waveform remains unchanged, inspect mel scaling/vocoder or acoustic perceptual dominance.'

        result['interpretation'] = {
            'diagnosis': diagnosis,
            'explanation': explanation,
            'delta_order': {
                'fs2_condition_local': fs2_delta,
                'auxiliary_mel_local': aux_delta,
                'diffusion_mel_local': diff_delta,
            },
        }

        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    finally:
        sys.argv = old_argv
        os.chdir(old_cwd)


if __name__ == '__main__':
    raise SystemExit(main())
