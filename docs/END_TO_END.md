# PhoenixVoiceEngine — End-to-End Workflow

## Target workflow

1. Upload an authorized clean/dry vocal.
2. Validate format, sample rate, channels and quality.
3. Transcribe Arabic lyrics with word timestamps.
4. Review/correct the transcript before generation.
5. Extract melody, notes, phrases, ornaments and other performance descriptors.
6. Store all analysis in the project manifest/profile.
7. Submit reference vocal + original lyrics + target lyrics + melody reference to a real singing backend.
8. Render the generated vocal.
9. Run post-generation quality checks.
10. Only then export the final WAV.

## Important engineering boundary

Phoenix is the orchestration and analysis layer. A scalar "voice DNA" score is not a trained singer model, and concatenating stored word WAVs is not acceptable as a production singing synthesizer.

The repository therefore uses `SynthesisBackend` as a hard boundary. A model backend must explicitly provide the actual singing generation/editing implementation.

## Arabic requirement

Arabic transcription is implemented in the Phoenix layer. The synthesis backend must be verified for Arabic singing before it is enabled for Arabic generation. Do not silently fall back to an English/Chinese-only model.

## Recommended backend evaluation

Evaluate at least two research backends against the same held-out Arabic test phrase:

- timbre similarity
- melody preservation
- lyric intelligibility
- timing preservation
- vibrato/ornament preservation
- noise/reverb/artifact level
- 44.1/48 kHz output quality

The backend that passes the acceptance thresholds becomes the production backend.

## Local UI

Run:

```text
python app.py
```

The UI creates a project, extracts Arabic words, saves a manifest, and exposes a target-lyrics generation step.

## Backend configuration

Set `PHOENIX_SYNTH_COMMAND` to the installed and authorized model adapter. The command must create the `{output_audio}` file and accept the supported placeholders documented in `src/synthesis/command_backend.py`.

## Safety and rights

Only use voices and recordings for which the operator has permission. The system should not be used to impersonate a real person without authorization.
