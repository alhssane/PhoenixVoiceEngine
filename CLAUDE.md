# Claude Code Instructions — Phoenix G2P Rewrite V1

## Scope

Work only on branch `phoenix-g2p-rewrite-v1`.
Do not modify or merge `main` as part of this experiment.

## Goal

Build and validate a production-safe Arabic G2P frontend for PhoenixVoiceEngine that can be used by the existing DiffSinger pipeline.

Required path:

Arabic text
-> real Phoenix Arabic G2P v02
-> Phoenix canonical phoneme contract
-> DiffSinger-compatible phone sequence

## Existing runtime artifacts

The real Phoenix G2P implementation is local and external to this repository:

`D:\PhoenixVoiceEngine\external\YingMusic-Singer-Plus\phoenix_arabic_g2p_v02.py`

The local runtime also contains:

`D:\PhoenixVoiceEngine\external\YingMusic-Singer-Plus\phoenix_arabic_token_map_v02.json`

Do not vendor large model/checkpoint binaries into this branch.

## Baseline protection

Do not modify or overwrite:

`phoenix_freed_joud_clean_v1`

or its `model_ckpt_steps_1600.ckpt` baseline.

Do not blindly enlarge an existing trained DiffSinger vocabulary. A vocabulary change requires a new model build and explicit compatibility checks.

## Important technical findings

The shared contract is:

`src/arabic/phoneme_contract.py`

It maps IPA to Phoenix canonical phones, including:

- `ʔ -> <`
- `ħ -> H`
- `ʕ -> ^`
- `ɣ -> g`

Long vowels become canonical `aa/ii/uu` and may later be normalized for a specific DiffSinger model.

The current trained baseline has:

`model.fs2.txt_embed.weight = (30, 256)`

Therefore its trained text-phone vocabulary is limited. Do not make a larger dictionary appear valid by editing only `phonemes.txt`.

## Validation targets

Always test at least:

- `عمر`
- `الكون`
- `الدنيا`
- `الحسن`
- `باني`
- `نور`

Expected canonical examples from the current real G2P + contract:

- `عمر -> ^ u m r`
- `الحسن -> < a l H a s a n`
- `الكون -> < a l k a w n`
- `الدنيا -> < a d d u n y aa`

## Engineering rule

Do not claim that a G2P change fixes synthesis quality until the complete path has been tested:

G2P -> canonical phones -> tokenization -> model input -> acoustic output -> vocoder WAV.

Prefer small, reproducible tests over starting new training runs prematurely.
