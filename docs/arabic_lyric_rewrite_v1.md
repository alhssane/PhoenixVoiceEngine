# Arabic Lyric Rewrite V1

This stage connects the Phoenix Arabic G2P frontend to the protected Freed Joud acoustic checkpoint.

## What it does

The adapter takes:

1. New Arabic text.
2. A reference DS file containing the melody/F0 timeline.
3. The trained checkpoint dictionary.

It produces a new DS file where:

- Arabic text is converted through the real Phoenix G2P v03.
- Canonical phones are normalized through `src/arabic/model_phone_contract.py` for the active baseline.
- `aa/ii/uu` are normalized to `a/i/u`, matching the established Stage4/Stage6 representation.
- The checkpoint vocabulary is checked before inference.
- Reference `f0_seq` and `f0_timestep` are preserved.
- Reference rest regions become `SP`.
- Each voiced note receives exactly one lyric syllable in V1.
- The vowel receives most of each note's duration.
- Total duration is preserved.

## Why this is the correct first fix

The direct acoustic DiffSinger path consumes the phoneme sequence, phoneme durations, and F0 curve. The reference F0 therefore remains the melody while the G2P output supplies the new linguistic content.

This is deliberately separate from model retraining. If a new lyric uses a phone that is absent from the protected checkpoint vocabulary, the adapter stops instead of producing a misleading result.

## Windows example

From `D:\PhoenixVoiceEngine`:

```powershell
& "D:\PhoenixVoiceEngine\.venv_phoenix_svs\Scripts\python.exe" `
  "D:\PhoenixVoiceEngine\scripts\rewrite_arabic_lyrics_g2p_melody_lock_v1.py" `
  --text "اكتب هنا كلمات الزفة الجديدة" `
  --reference-ds "D:\PhoenixVoiceEngine\jobs\freed_joud_full_auto\inference\freed_joud_stage10.ds" `
  --output "D:\PhoenixVoiceEngine\jobs\freed_joud_full_auto\inference\rewritten_lyrics_v1.ds"
```

Then synthesize with the protected checkpoint using the existing DiffSinger `scripts\infer.py` acoustic command.

Do not start a new training run for this V1 test.

## V1 limitation

The lyric must contain exactly one syllable for every voiced note in the reference melody. This is intentional: it prevents us from hiding a bad lyric-to-melody alignment behind arbitrary duration stretching.

After a successful V1 listening test, V2 can add controlled multi-note syllable/melisma mapping.
