# Phoenix Voice Studio

Phoenix Voice Studio is an AI singing-production workspace focused on analysis, lyric editing, performance preservation and pluggable singing synthesis backends.

## Current Architecture

- **Project layer** — reproducible project folders and manifests.
- **Audio layer** — inspection and preparation of clean vocal input.
- **Arabic lyrics layer** — word-level transcription with timestamps.
- **Performance analysis** — pitch/note/phrase/ornament-oriented analysis already present in `src/analysis`.
- **Human lyric review** — existing review UI protects the original transcript.
- **Synthesis boundary** — `src/synthesis/synthesis_backend.py` defines the contract for a real singing model.
- **Local UI** — `python app.py` launches the end-to-end workflow.

## Intended User Flow

1. Add an authorized dry/acapella vocal.
2. Analyze the recording.
3. Extract and review Arabic lyrics.
4. Build the project analysis package.
5. Enter new lyrics, a new couplet, or a full replacement section.
6. Send the original vocal/melody reference and target lyrics to the configured singing backend.
7. Validate and export the generated WAV.

## Important Boundary

Phoenix does **not** pretend that a few handcrafted numbers are a trained singer model, and it does not reconstruct singing by concatenating isolated word recordings. The synthesis backend must perform the actual neural singing generation/editing.

Arabic generation is enabled only when the configured backend explicitly supports Arabic singing. This prevents silent fallback to a model trained for another language.

## Development

```text
python app.py
python -m pytest -q
```

See `docs/END_TO_END.md` for the production workflow and backend acceptance criteria.
