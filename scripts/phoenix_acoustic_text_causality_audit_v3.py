from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from pathlib import Path
from typing import Any

import torch


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def set_seed(seed: int) -> None:
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)


def load_one_segment(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8-sig"))
    if isinstance(payload, dict):
        segment = payload
    elif isinstance(payload, list) and len(payload) == 1 and isinstance(payload[0], dict):
        segment = payload[0]
    else:
        raise RuntimeError(
            "Control DS must be one segment: either a JSON object or a one-element JSON list."
        )
    for key in ("ph_seq", "ph_dur", "f0_seq", "f0_timestep"):
        if key not in segment:
            raise RuntimeError(f"Control DS missing required field: {key}")
    return segment


def clone_phone_mutation(
    segment: dict[str, Any], start: int, expect: list[str], replace: list[str]
) -> dict[str, Any]:
    phones = str(segment["ph_seq"]).split()
    end = start + len(expect)
    observed = phones[start:end]
    if observed != expect:
        raise RuntimeError(
            f"Reference guard failed at {start}:{end}: expected {expect}, observed {observed}."
        )
    if len(replace) != len(expect):
        raise RuntimeError("Mutation requires equal-length replacement.")
    out = dict(segment)
    mutated = list(phones)
    mutated[start:end] = replace
    out["ph_seq"] = " ".join(mutated)
    return out


def _mask_tensor(t: torch.Tensor, mask: torch.Tensor) -> torch.Tensor:
    """Apply a [T] frame mask to tensors shaped [B,T,...] or [T,...]."""
    x = t.detach().float()
    m = mask.detach().bool()

    if x.ndim == 0:
        raise RuntimeError("Cannot mask a scalar tensor.")

    if x.ndim >= 2 and x.shape[0] == 1 and x.shape[1] == m.shape[0]:
        return x[:, m, ...]

    if x.ndim >= 1 and x.shape[0] == m.shape[0]:
        return x[m, ...]

    raise RuntimeError(
        f"Mask shape {tuple(m.shape)} is incompatible with tensor shape {tuple(x.shape)}."
    )


def rel_l2(a: torch.Tensor, b: torch.Tensor, mask: torch.Tensor | None = None) -> float:
    x = _mask_tensor(a, mask) if mask is not None else a.detach().float()
    y = _mask_tensor(b, mask) if mask is not None else b.detach().float()
    denom = max(float(x.norm().cpu()), 1e-8)
    return float((x - y).norm().cpu()) / denom


def cosine_distance(
    a: torch.Tensor, b: torch.Tensor, mask: torch.Tensor | None = None
) -> float:
    x = _mask_tensor(a, mask) if mask is not None else a.detach().float()
    y = _mask_tensor(b, mask) if mask is not None else b.detach().float()
    x = x.reshape(-1)
    y = y.reshape(-1)
    denom = max(float(x.norm().cpu() * y.norm().cpu()), 1e-8)
    return 1.0 - float(torch.dot(x, y).cpu()) / denom


def main() -> int:
    ap = argparse.ArgumentParser(description="Phoenix DiffSinger acoustic text-causality audit v3.")
    ap.add_argument("--diffsinger-root", required=True)
    ap.add_argument("--exp", required=True)
    ap.add_argument("--ckpt", type=int, required=True)
    ap.add_argument("--checkpoint-file", type=Path, required=True)
    ap.add_argument("--control-ds", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    ap.add_argument("--start-phone", type=int, default=11)
    ap.add_argument("--expect", nargs="+", default=["n", "f", "i"])
    ap.add_argument("--replace", nargs="+", default=["b", "a", "b"])
    ap.add_argument("--seed", type=int, default=20260831)
    args = ap.parse_args()

    root = Path(args.diffsinger_root).resolve()
    control_path = args.control_ds.resolve()
    checkpoint_file = args.checkpoint_file.resolve()
    output = args.output.resolve()
    for p in (root, control_path, checkpoint_file):
        if not p.exists():
            raise FileNotFoundError(p)

    os.environ["PYTHONPATH"] = str(root)
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))

    control_param = load_one_segment(control_path)
    mutant_param = clone_phone_mutation(
        control_param, args.start_phone, args.expect, args.replace
    )

    old_cwd = Path.cwd()
    old_argv = sys.argv[:]
    try:
        os.chdir(root)
        sys.argv = [
            "phoenix_acoustic_text_causality_audit_v3.py",
            "--exp_name",
            args.exp,
            "--infer",
        ]
        from utils.hparams import set_hparams, hparams
        set_hparams(print_hparams=False)

        from inference.ds_acoustic import DiffSingerAcousticInfer
        infer = DiffSingerAcousticInfer(load_vocoder=False, ckpt_steps=args.ckpt)

        def prepare(segment: dict[str, Any]) -> dict[str, torch.Tensor]:
            p = dict(segment)
            p.setdefault("lang", "ar")
            return infer.preprocess_input(p, idx=0)

        control = prepare(control_param)
        mutant = prepare(mutant_param)
        if tuple(control["mel2ph"].shape) != tuple(mutant["mel2ph"].shape):
            raise RuntimeError("Control/mutant mel2ph shapes differ.")

        mel2ph = control["mel2ph"][0]
        p0 = args.start_phone + 1
        p1 = args.start_phone + len(args.expect)
        local_mask = (mel2ph >= p0) & (mel2ph <= p1)
        if not bool(local_mask.any()):
            raise RuntimeError("Mutation produced an empty local mel2ph mask.")

        with torch.no_grad():
            c_tokens = control["tokens"]
            m_tokens = mutant["tokens"]
            c_txt = infer.model.fs2.txt_embed(c_tokens)
            m_txt = infer.model.fs2.txt_embed(m_tokens)
            c_condition = infer.model.fs2(c_tokens, control["mel2ph"], control["f0"])
            m_condition = infer.model.fs2(m_tokens, mutant["mel2ph"], mutant["f0"])

            if not hasattr(infer.model, "aux_decoder"):
                raise RuntimeError("Model has no aux_decoder; shallow-diffusion audit cannot continue.")
            if not hasattr(infer.model, "diffusion"):
                raise RuntimeError("Model has no diffusion module; audit cannot continue.")

            set_seed(args.seed)
            c_aux = infer.model.aux_decoder(c_condition, infer=True)
            set_seed(args.seed)
            m_aux = infer.model.aux_decoder(m_condition, infer=True)
            set_seed(args.seed)
            c_diff = infer.model.diffusion(c_condition, src_spec=c_aux, infer=True)
            set_seed(args.seed)
            m_diff = infer.model.diffusion(m_condition, src_spec=m_aux, infer=True)

        metrics = {
            "text_embedding_relative_l2": rel_l2(c_txt, m_txt),
            "fs2_condition_local_relative_l2": rel_l2(c_condition, m_condition, local_mask),
            "fs2_condition_global_relative_l2": rel_l2(c_condition, m_condition),
            "auxiliary_mel_local_relative_l2": rel_l2(c_aux, m_aux, local_mask),
            "auxiliary_mel_global_relative_l2": rel_l2(c_aux, m_aux),
            "auxiliary_mel_local_cosine_distance": cosine_distance(c_aux, m_aux, local_mask),
            "diffusion_mel_local_relative_l2": rel_l2(c_diff, m_diff, local_mask),
            "diffusion_mel_global_relative_l2": rel_l2(c_diff, m_diff),
            "diffusion_mel_local_cosine_distance": cosine_distance(c_diff, m_diff, local_mask),
        }

        fs2 = metrics["fs2_condition_local_relative_l2"]
        aux = metrics["auxiliary_mel_local_relative_l2"]
        diff = metrics["diffusion_mel_local_relative_l2"]
        if aux < max(fs2 * 0.25, 1e-4):
            diagnosis = "TEXT_EFFECT_COLLAPSES_BEFORE_OR_AT_AUX_MEL"
        elif diff < max(aux * 0.25, 1e-4):
            diagnosis = "TEXT_EFFECT_COLLAPSES_IN_DIFFUSION"
        else:
            diagnosis = "TEXT_EFFECT_SURVIVES_TO_FINAL_MEL"

        result = {
            "status": "PHOENIX_ACOUSTIC_TEXT_CAUSALITY_AUDIT_V3",
            "exp": args.exp,
            "ckpt": args.ckpt,
            "checkpoint_file": str(checkpoint_file),
            "checkpoint_sha256": sha256_file(checkpoint_file),
            "control_ds": str(control_path),
            "mutation": {
                "start_phone": args.start_phone,
                "end_phone_exclusive": args.start_phone + len(args.expect),
                "expect": args.expect,
                "replace": args.replace,
                "changed_field": "ph_seq",
                "local_frame_count": int(local_mask.sum().item()),
            },
            "config": {
                "audio_sample_rate": hparams.get("audio_sample_rate"),
                "audio_num_mel_bins": hparams.get("audio_num_mel_bins"),
                "hop_size": hparams.get("hop_size"),
                "hidden_size": hparams.get("hidden_size"),
                "use_shallow_diffusion": hparams.get("use_shallow_diffusion"),
                "diffusion_type": hparams.get("diffusion_type"),
                "use_pos_embed": hparams.get("use_pos_embed"),
                "use_lang_id": hparams.get("use_lang_id"),
                "shallow_diffusion_args": hparams.get("shallow_diffusion_args"),
            },
            "shapes": {
                "tokens": list(control["tokens"].shape),
                "mel2ph": list(control["mel2ph"].shape),
                "f0": list(control["f0"].shape),
                "text_embedding": list(c_txt.shape),
                "condition": list(c_condition.shape),
                "aux_mel": list(c_aux.shape),
                "diffusion_mel": list(c_diff.shape),
            },
            "metrics": metrics,
            "interpretation": {
                "diagnosis": diagnosis,
                "delta_order": {
                    "fs2_condition_local": fs2,
                    "auxiliary_mel_local": aux,
                    "diffusion_mel_local": diff,
                },
            },
        }

        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    finally:
        sys.argv = old_argv
        os.chdir(old_cwd)


if __name__ == "__main__":
    raise SystemExit(main())
