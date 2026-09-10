# PhoenixVoiceEngine — Working Rules

## Repository authority

`main` is the canonical project branch and the source of truth for implementation decisions.
Do not restart completed stages merely because an older conversation described them differently.
Before changing code, inspect the current GitHub state and the latest validated progress.

## Protected acoustic baseline

The verified Freed Joud acoustic baseline is:

- experiment: `phoenix_freed_joud_clean_v1`
- checkpoint: `model_ckpt_steps_1600.ckpt`
- baseline purpose: preserve the clear/very-good reference result already verified by human listening.

Never overwrite or delete this checkpoint during lyric-rewrite work.

## Arabic G2P

The real runtime G2P is external to this repository:

`D:\PhoenixVoiceEngine\external\YingMusic-Singer-Plus\phoenix_arabic_g2p_v03.py`

The repository frontend is:

`src/arabic/g2p_frontend.py`

Required path for lyric rewriting:

Arabic text
-> Phoenix Arabic G2P v03
-> Phoenix canonical phones
-> model-specific phone normalization
-> checkpoint vocabulary gate
-> DiffSinger DS with preserved F0/timing
-> acoustic inference
-> WAV listening test

A G2P smoke test passing by itself is not proof of synthesis compatibility.

## Phone vocabulary rule

The acoustic checkpoint has a fixed trained text vocabulary. Never make an unseen phone appear valid by editing a dictionary alone.

If a new lyric produces a phone absent from the checkpoint dictionary, stop and report the missing phone. A vocabulary expansion requires a compatible new training run.

Model-phone normalization must be explicit and centralized. The current Stage4/Stage6 baseline maps `aa/ii/uu` to `a/i/u`; this changes representation without inventing a new sound class because vowel duration remains represented by `ph_dur`.

## Lyric rewrite rule

The first safe lyric-rewrite path is intentionally strict:

- preserve the reference `f0_seq` and `f0_timestep`
- preserve the reference note/rest timeline
- require one lyric syllable per voiced note
- insert `SP` for reference rest regions
- normalize `aa/ii/uu` to `a/i/u` through the shared model-phone contract
- derive new `ph_dur` inside each note, with the vowel receiving most of the note duration
- do not start a new training run until the direct-acoustic rewrite path is proven

Script:

`scripts/rewrite_arabic_lyrics_g2p_melody_lock_v1.py`

This V1 is a direct acoustic path. Its `ph_num` is not intended to drive variance duration prediction.

## Validation order

1. Run the G2P probe.
2. Generate a rewritten DS.
3. Inspect the rewritten DS invariants and vocabulary gate.
4. Run acoustic inference with the protected checkpoint.
5. Listen to the WAV.
6. Only after the audio passes, consider V2 melody fitting or additional training.

## No silent regressions

Do not silently replace a verified checkpoint, config, dictionary, phone contract, or reference audio. Version changes explicitly and preserve successful artifacts.
