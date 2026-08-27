from __future__ import annotations

import argparse
import json
from pathlib import Path

from src.transcription.gemini_audio_transcription_engine import transcribe_audio


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Transcribe a complete song with Gemini 3.5 Transcribe and word timestamps."
    )
    ap.add_argument("--source-wav", required=True)
    ap.add_argument("--output", required=True)
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

    print(
        json.dumps(
            {
                "status": result["status"],
                "model": result["model"],
                "audio_duration_sec": result["audio"]["duration_sec"],
                "word_count": result["word_count"],
                "last_word_end_sec": result["validation"]["last_word_end_sec"],
                "output": str(Path(args.output).resolve()),
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
