# Phoenix Voice Studio

Phoenix Voice Studio is an AI singing-production workspace focused on analysis, lyric editing, performance preservation and pluggable singing synthesis backends.

## Current Architecture

- **Project layer** — reproducible project folders and manifests.
- **Audio layer** — inspection and preparation of clean vocal input.
- **Arabic lyrics layer** — word-level transcription with timestamps and an Arabic G2P front-end.
- **Performance analysis** — pitch/note/phrase/ornament-oriented analysis already present in `src/analysis`.
- **Human lyric review** — existing review UI protects the original transcript.
- **Synthesis boundary** — `src/synthesis/synthesis_backend.py` defines the contract for a real singing model.
- **Production bridge** — `ProductionSingingBackend` writes a complete Arabic generation manifest and refuses to claim success without a real model and a valid WAV.
- **Local UI** — `python app.py` launches the end-to-end workflow.

## Intended User Flow

1. Add an authorized dry/acapella vocal.
2. Analyze the recording.
3. Extract and review Arabic lyrics.
4. Build the project analysis package.
5. Enter new lyrics, a new couplet, or a full replacement section.
6. Preserve the reference melody/performance descriptors and send the request to the configured Arabic-capable singing backend.
7. Render the generated WAV.
8. Validate the output before export.

## Important Boundary

Phoenix does **not** pretend that a few handcrafted numbers are a trained singer model, and it does not reconstruct singing by concatenating isolated word recordings. The synthesis backend must perform the actual neural singing generation/editing.

Arabic generation is enabled only when the configured backend explicitly supports Arabic singing. This prevents silent fallback to a model trained for another language.

## Development

```text
python app.py
python -m pytest -q
```

See `docs/END_TO_END.md` for the production workflow and backend acceptance criteria.
