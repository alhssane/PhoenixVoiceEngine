# Phoenix G2P Rewrite V1

This branch is an isolated G2P/frontend experiment. It is intentionally based on `main` and does not modify the existing Baseline checkpoints or training pipeline.

## Scope

- Load the real local `phoenix_arabic_g2p_v02.py` runtime artifact.
- Convert Arabic text to the Phoenix canonical phone contract already present in `src/arabic/phoneme_contract.py`.
- Keep the G2P frontend separate from DiffSinger model training/inference.
- Fail closed when G2P or canonicalization fails.
- Provide smoke tests for new words such as `عمر` and `الحسن`.

## Runtime dependency

The real G2P implementation is external to this repository by design:

`D:\PhoenixVoiceEngine\external\YingMusic-Singer-Plus\phoenix_arabic_g2p_v02.py`

Override it with:

`PHOENIX_ARABIC_G2P_MODULE_PATH`

`phonemizer` and eSpeak-NG must be installed in the runtime environment.

## Important boundary

This branch does **not** enlarge the trained DiffSinger vocabulary and does **not** modify the existing `phoenix_freed_joud_clean_v1` checkpoint. Phone-vocabulary expansion is a separate model-build decision and must be validated before training.

## Smoke test

From the PhoenixVoiceEngine environment:

```powershell
python scripts/probe_phoenix_g2p_frontend.py
```

Expected examples from the current runtime contract:

- `عمر` -> `^ u m r`
- `الحسن` -> `< a l H a s a n`
