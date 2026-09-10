# PhoenixVoiceEngine — Arabic New-Word Pronunciation Root-Cause Audit V1

## Scope

This audit focuses on the path that should allow a new Arabic lyric to be sung with a trained artist voice while preserving the reference melody and timing.

## Confirmed architecture contract

The repository rules define a strict path:

Arabic text -> Phoenix Arabic G2P -> canonical phones -> model-specific phone normalization -> checkpoint vocabulary gate -> DiffSinger DS with preserved F0/timing -> acoustic inference -> listening test.

G2P success alone is explicitly not considered proof of synthesis compatibility.

## Findings

### 1. The repository had a real phoneme conversion defect

`src/synthesis/lyric_to_phoneme_engine.py` previously split an Arabic word into Unicode characters. That is not a phoneme representation and cannot reliably encode Arabic long vowels, emphatics, digraphs, or other phone distinctions.

This has been corrected on this branch to route lyric conversion through `PhoenixArabicG2PFrontend`.

### 2. The project frontend default was stale

The repository frontend and tests previously defaulted to Phoenix Arabic G2P v02 while the current project runtime uses v03. This created a version skew risk between the code contract and the actually validated G2P runtime.

This branch updates the repository default to v03 while preserving an environment-variable override for explicit alternate installations.

### 3. Model-phone normalization was duplicated

The lyric rewrite script contained its own `aa/ii/uu -> a/i/u` mapping. The canonical phone contract separately defines long vowels. Having multiple normalization definitions is a reproducibility risk.

This branch adds `src/arabic/model_phone_contract.py` and routes lyric rewriting through it.

### 4. Letter-based duration learning is not a safe pronunciation model

`src/trainer/artist_pronunciation_learning_engine.py` currently learns duration statistics per Arabic letter, not per G2P phoneme. This is not sufficient to model pronunciation behavior for new words.

`src/synthesis/phoneme_database_engine.py` similarly divides word duration across letters. Those modules should not be treated as the authoritative pronunciation-learning path for the neural singing model until they are replaced by phoneme-aligned data.

### 5. Word duration estimation is currently heuristic

`src/lyrics/word_duration_mapper.py` estimates target duration from character count. This is not linguistically grounded and should not be used as the source of neural pronunciation timing. The authoritative direct-acoustic path should preserve the reference musical timeline and explicitly allocate phoneme duration within each note.

### 6. The repository already has the correct safety principle for new phones

The lyric rewrite adapter rejects phones absent from the selected checkpoint vocabulary instead of silently changing a dictionary to make them appear valid.

## Current training lesson

The validated experiments show that the text conditioning path can change when `n u r` is replaced by `d a r`; therefore, the observed V16 failure cannot be explained simply by the inference frontend ignoring the new phoneme sequence.

The repository-level conclusion is that model-quality diagnosis must separate:

1. phone generation correctness,
2. checkpoint vocabulary compatibility,
3. phoneme-duration/alignment correctness,
4. transfer of learned text/phoneme embeddings during fine-tuning,
5. acoustic generalization to unseen sequences.

The exact fine-tuning loader behavior for `finetune_ignored_params` belongs to the external OpenVPI DiffSinger source and is therefore not inferable from this repository alone. That external code must be inspected before declaring text-embedding transfer behavior as the cause.

## Branch status

This audit branch contains repository-level fixes and regression coverage. No checkpoint, generated Binary, or large training corpus is stored in GitHub as part of this change.
