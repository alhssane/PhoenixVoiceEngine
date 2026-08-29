from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

import torch


def main() -> int:
    parser = argparse.ArgumentParser(description="Trace DiffSinger text conditioning without modifying weights.")
    parser.add_argument("--diffsinger-root", required=True)
    parser.add_argument("--exp", required=True)
    parser.add_argument("--ckpt", type=int, required=True)
    parser.add_argument("--ds", required=True)
    parser.add_argument("--lang", default="ar")
    args = parser.parse_args()

    root = Path(args.diffsinger_root).resolve()
    ds_path = Path(args.ds).resolve()
    if not root.is_dir():
        raise FileNotFoundError(root)
    if not ds_path.is_file():
        raise FileNotFoundError(ds_path)

    os.environ["PYTHONPATH"] = str(root)
    sys.path.insert(0, str(root))

    from utils.hparams import set_hparams
    from inference.ds_acoustic import DiffSingerAcousticInfer

    params = json.loads(ds_path.read_text(encoding="utf-8-sig"))
    if not isinstance(params, list):
        params = [params]
    for param in params:
        param.setdefault("lang", args.lang)

    old_argv = sys.argv[:]
    try:
        sys.argv = ["trace_diffsinger_text_path_v1.py", "--exp_name", args.exp, "--infer"]
        set_hparams()
    finally:
        sys.argv = old_argv

    infer = DiffSingerAcousticInfer(load_vocoder=False, ckpt_steps=args.ckpt)
    phone_to_id = infer.phoneme_dictionary._phone_to_id

    print("=== DIFFSINGER TEXT CONDITION TRACE V1 ===")
    print("EXP:", args.exp)
    print("CKPT:", args.ckpt)
    print("DS:", ds_path)
    print("PHONE_DICT_SIZE:", len(infer.phoneme_dictionary))

    for idx, param in enumerate(params):
        print(f"\n--- SEGMENT {idx} ---")
        print("PH_SEQ:", param["ph_seq"])
        batch = infer.preprocess_input(param, idx=idx)
        tokens = batch["tokens"]
        print("TOKENS_SHAPE:", tuple(tokens.shape))
        print("TOKEN_IDS:", tokens[0].detach().cpu().tolist())
        print("PHONE_TO_ID:", [(p, phone_to_id.get(p)) for p in param["ph_seq"].split()])
        print("MEL2PH_SHAPE:", tuple(batch["mel2ph"].shape))
        print("F0_SHAPE:", tuple(batch["f0"].shape))

        with torch.no_grad():
            txt_embed = infer.model.fs2.txt_embed(tokens)
            print("TXT_EMBED_SHAPE:", tuple(txt_embed.shape))
            print("TXT_EMBED_NORM_TOTAL:", round(float(txt_embed.norm().cpu()), 8))
            print("TXT_EMBED_TOKEN_NORMS:", [round(float(v), 6) for v in txt_embed[0].norm(dim=-1).cpu()])

            condition = infer.model.fs2(tokens, batch["mel2ph"], batch["f0"])
            print("FS2_CONDITION_SHAPE:", tuple(condition.shape))
            print("FS2_CONDITION_NORM_TOTAL:", round(float(condition.norm().cpu()), 8))

            candidates = [phone_to_id[p] for p in ("a", "b", "n", "r", "^") if p in phone_to_id]
            tested = False
            for pos in range(tokens.shape[1]):
                original = int(tokens[0, pos].item())
                replacement = next((x for x in candidates if x != original), None)
                if original == 0 or replacement is None:
                    continue
                mutant = tokens.clone()
                mutant[0, pos] = replacement
                mutant_condition = infer.model.fs2(mutant, batch["mel2ph"], batch["f0"])
                delta = mutant_condition - condition
                relative = float(delta.norm().cpu()) / max(float(condition.norm().cpu()), 1e-8)
                print("COUNTERFACTUAL_POSITION:", pos)
                print("COUNTERFACTUAL_ORIGINAL_ID:", original)
                print("COUNTERFACTUAL_REPLACEMENT_ID:", replacement)
                print("COUNTERFACTUAL_RELATIVE_FS2_DELTA:", round(relative, 8))
                tested = True
                break
            print("TOKEN_SENSITIVITY_TESTED:", tested)

    print("\nSTATUS: DIFFSINGER_TEXT_CONDITION_TRACE_COMPLETE")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
