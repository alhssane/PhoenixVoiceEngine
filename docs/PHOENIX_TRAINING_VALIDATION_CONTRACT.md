# PhoenixVoiceEngine — Training Validation Contract

## Purpose

This contract is project-wide. It applies to every future training job and every source audio item, not only the current `freed_joud` job.

The goal is to prevent long training runs from hiding defects in preprocessing, alignment, spectral representation, or the vocoder path.

## Mandatory gates

Every training job must pass these gates in order:

1. **Transcript gate**
   - Canonical UTF-8 Arabic text.
   - No mojibake.
   - Timing is valid and covers the intended spoken/sung content.
   - Forbidden/non-lyric boilerplate is rejected according to the project transcript policy.

2. **Arabic phone-contract gate**
   - Every training word must convert through the single Phoenix Arabic phoneme contract.
   - Every emitted phone must exist in the configured DiffSinger vocabulary.
   - No script may silently substitute a second, incompatible IPA-to-phone mapping.

3. **Segmentation/alignment gate**
   - No word may be split across segment boundaries.
   - Stage alignment must account for the complete timed word span.
   - Partial-word or missing-audio conditions must fail closed.

4. **Acoustic feature gate**
   - Training WAVs must be validated at the configured acoustic sample rate.
   - Ground-truth Mel and F0 must be generated with the same feature functions/parameters used by the target DiffSinger acoustic configuration.
   - F0 coverage and non-finite-value checks must pass.

5. **Ground-truth vocoder gate — mandatory before long training**
   - At least one real training WAV must be reconstructed using **ground-truth Mel + ground-truth F0 + the exact project vocoder checkpoint**, without the acoustic model.
   - The reconstruction must be audibly acceptable and must pass objective sanity checks (finite audio, expected sample rate, non-empty output).
   - This is a project-level prerequisite for starting any long acoustic training run.

6. **Dataset/binary integrity gate**
   - Train/validation item counts, phone IDs, durations, Mel frame counts, and binary tensor integrity must pass.

7. **Training smoke gate**
   - A fresh small-step training run must complete from the intended initialization mode.
   - The run must not accidentally restore an unrelated experiment/checkpoint.

8. **Checkpoint/inference gate**
   - Checkpoint loading must be verified explicitly.
   - A short inference output must be generated before committing to a longer run.
   - For diagnosis, the project must preserve the predicted Mel/F0 when practical so that acoustic-model and vocoder stages can be tested independently.

## Global invariant

The vocoder is treated as an independently testable component. A bad synthesized waveform must not be attributed to training until the ground-truth vocoder reconstruction passes.

## Current proven baseline

The current Phoenix V2 job demonstrated that the ground-truth path can produce a good reconstruction using the project PC-NSF-HiFiGAN configuration:

- 44.1 kHz audio
- 128 Mel bins
- hop size 512
- Parselmouth F0
- PC-NSF-HiFiGAN checkpoint `pc_nsf_hifigan_44.1k_hop512_128bin_2025.02/model.ckpt`

This is the reference behavior for future jobs.

## Required project behavior for new audio

When a new source audio item is added later, it must enter the same gates automatically. The workflow must not be hard-coded around the current song ID, speaker name, or folder name.

## What this contract does not claim

Passing the ground-truth vocoder gate does **not** prove that an acoustic model is well trained. It only proves that the feature representation and the project's vocoder path can reconstruct a real training signal acceptably. Acoustic-model quality remains a separate validation problem.
