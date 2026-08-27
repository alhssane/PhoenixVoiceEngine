from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.arabic.transcript_contract import load_words, write_words


def main() -> int:
    ap = argparse.ArgumentParser(description="Create the single canonical UTF-8 timed-word transcript for Phoenix.")
    ap.add_argument("--input", required=True)
    ap.add_argument("--output", required=True)
    args = ap.parse_args()

    source = Path(args.input).resolve()
    output = Path(args.output).resolve()
    if not source.is_file():
        raise FileNotFoundError(f"Transcript not found: {source}")

    words = load_words(source)
    write_words(output, words)

    report = {
        "status": "CANONICAL_TRANSCRIPT_READY",
        "input": str(source),
        "output": str(output),
        "word_count": len(words),
        "first_word": words[0]["word"],
        "last_word": words[-1]["word"],
    }
    report_path = output.with_name(output.stem + ".report.json")
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
