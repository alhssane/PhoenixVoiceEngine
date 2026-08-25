# Phoenix Voice Engine (PVE)

Version: 0.2.0
Status: Active Engineering

## Product Goal

Phoenix Voice Engine is an AI singing-editing platform. The target workflow is:

**clean vocal → Arabic lyric transcription → performance analysis → human lyric review → neural singing edit → quality validation → final WAV**

The system is designed for authorized recordings and voices only.

## Milestones

### Milestone 1 — Foundation

- [x] Project manager
- [x] Portable project paths
- [x] Metadata protection
- [x] Baseline CI
- [x] Unit-test boundary

### Milestone 2 — Analysis Package

- [x] Audio inspection
- [x] Arabic word-level transcription interface
- [x] Pitch/note analysis modules
- [x] Vocal signature analysis modules
- [x] Maqam/quarter-tone analysis modules
- [x] Lyric human-review UI
- [x] Project manifest

### Milestone 3 — Production Synthesis Boundary

- [x] Stable `SynthesisBackend` contract
- [x] External command adapter
- [x] End-to-end local UI
- [ ] Select Arabic-capable neural singing backend
- [ ] Benchmark timbre similarity
- [ ] Benchmark melody/prosody preservation
- [ ] Benchmark Arabic lyric intelligibility
- [ ] Add post-generation quality gate

### Milestone 4 — Release Candidate

- [ ] GPU environment installer
- [ ] Model download/cache manager
- [ ] One-click project preparation
- [ ] Full-section lyric editing
- [ ] WAV/FLAC export presets
- [ ] Regression audio benchmark set
- [ ] Final acceptance test on authorized reference material

## Non-negotiable engineering rules

1. Never hardcode a developer's local Windows path into production code.
2. Never fabricate an artist name, maqam, confidence, or quality score.
3. Never treat a scalar voice score as a trained model.
4. Never use word-file concatenation as a singing synthesizer.
5. Never silently use a backend that does not support the requested language.
6. Every model backend must have reproducible inference settings and an acceptance test.
7. Generated audio must pass technical quality checks before export.
