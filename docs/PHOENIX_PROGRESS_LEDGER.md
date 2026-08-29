# PhoenixVoiceEngine — Validated Progress Ledger

## Canonical project
- GitHub: alhssane/PhoenixVoiceEngine
- Canonical branch: main
- Goal: Arabic singing editing with OpenVPI DiffSinger, ultimately changing the zaffa lyrics by writing new Arabic text and evaluating the result by listening.

## Validated gates — DO NOT REPEAT
1. Arabic/DiffSinger dataset pipeline reached valid binary datasets.
2. `freed_joud_diffsinger_binary_full_v3`:
   - train items: 11
   - valid items: 2
   - required binary artifacts present
   - deep integrity checks passed
   - train/valid core tensors are structurally valid
3. Stage 7 binary integrity gate passed:
   - status: `STAGE7_BINARY_INTEGRITY_OK`
   - train: 11
   - valid: 2
   - token range: 1..28
   - train mel frames: 70..725
   - valid mel frames: 301..344
4. Stage 7 two-step training smoke passed on NVIDIA GeForce RTX 4070 Laptop GPU:
   - 74.0M trainable parameters
   - checkpoint at step 1 created
   - checkpoint at step 2 created
   - `max_steps=2` reached cleanly
   - this proves the training path/GPU/config can execute; it is NOT a quality result.
5. The next intended gate is controlled longer training followed by acoustic inference and ground-truth-vocoder listening.

## Current active path
- DiffSinger: OpenVPI
- Config: `configs/diffsinger/phoenix_arabic_acoustic.yaml`
- Canonical current binary for this path: `datasets/freed_joud_diffsinger_binary_full_v3`
- Stage 8 controlled training: 1000 steps
- Then checkpoint audit / compatibility gate
- Then inference and audible reconstruction
- Do not restart Stage 1–7 unless a later gate proves a regression.

## Important distinction
The 2-step smoke is only an execution/integrity gate. It does not establish singing quality, lyric-edit quality, or vocoder quality.

## Successful approach to preserve
- Use the established Arabic phoneme/duration dataset rather than rebuilding it.
- Use OpenVPI DiffSinger acoustic training as the current singing synthesis path.
- Validate binary integrity before training.
- Use short controlled smoke training before long training.
- Use actual acoustic inference and listening as the quality gate.
