from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# The CLI lives in scripts/, so explicitly add the repository root before
# importing the Phoenix package. This keeps direct invocation working on
# Windows without requiring PYTHONPATH to be set externally.
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.transcription.gemini_audio_transcription_engine import transcribe_audio


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Transcribe a complete song with Gemini 3.5 Transcribe and word timestamps."
    )
    ap.add_argument("--source-wav", required=True)
    ap.add_argument("--output", required=True, help="Detailed Gemini transcript report JSON")
    ap.add_argument("--words-output", default=None, help="Optional plain words-list JSON for Phoenix pipeline")
    ap.add_argument("--raw-output", default=None)
    ap.add_argument(
        "--language",
        action="append",
        dest="languages",
        help="BCP-47 language hint. May be supplied multiple times; default is automatic detection.",
    )
    ap.add_argument(
        "--vocabulary",
        default=None,
        help="Optional UTF-8 JSON list of custom vocabulary terms.",
    )
    args = ap.parse_args()

    vocabulary = None
    if args.vocabulary:
        vocabulary_path = Path(args.vocabulary).resolve()
        data = json.loads(vocabulary_path.read_text(encoding="utf-8"))
        if not isinstance(data, list) or not all(isinstance(x, str) for x in data):
            raise SystemExit("Vocabulary JSON must be a list of strings.")
        vocabulary = data

    result = transcribe_audio(
        audio_path=args.source_wav,
        output_path=args.output,
        language_codes=args.languages or [],
        custom_vocabulary=vocabulary,
        raw_output_path=args.raw_output,
    )

    if args.words_output:
        words_path = Path(args.words_output).resolve()
        words_path.parent.mkdir(parents=True, exist_ok=True)
        words_path.write_text(
            json.dumps(result["words"], ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    print(
        json.dumps(
            {
                "status": result["status"],
                "model": result["model"],
                "audio_duration_sec": result["audio"]["duration_sec"],
                "word_count": result["word_count"],
                "last_word_end_sec": result["validation"]["last_word_end_sec"],
                "output": str(Path(args.output).resolve()),
                "words_output": str(Path(args.words_output).resolve()) if args.words_output else None,
                "training_allowed": result["training_allowed"],
                "next_gate": result["next_gate"],
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
