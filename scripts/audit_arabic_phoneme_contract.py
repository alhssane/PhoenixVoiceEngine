from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.arabic.phoneme_contract import phonemize_arabic_word
from src.arabic.transcript_contract import load_words


def load_dictionary(path: Path) -> set[str]:
    text = path.read_text(encoding="utf-8")
    parts = text.split()
    if parts and parts[0].upper().startswith("PHOENIX_"):
        parts = parts[1:]
    return set(parts)


def main() -> int:
    ap = argparse.ArgumentParser(description="Audit Arabic transcript -> canonical Phoenix phones")
    ap.add_argument("--words-json", required=True)
    ap.add_argument("--dictionary", required=False)
    ap.add_argument("--output", required=True)
    args = ap.parse_args()

    words = load_words(Path(args.words_json).resolve())
    from epitran import Epitran
    epi = Epitran("ara-Arab")

    dictionary = load_dictionary(Path(args.dictionary).resolve()) if args.dictionary else None
    rows = []
    failures = []
    for index, item in enumerate(words):
        word = item["word"]
        try:
            conv = phonemize_arabic_word(epi, word)
            phones = list(conv.phones)
            missing = sorted(set(phones) - dictionary) if dictionary is not None else []
            row = {"index": index, "word": word, "ipa": conv.ipa, "phones": phones, "dictionary_missing": missing, "status": "OK" if not missing else "DICTIONARY_MISMATCH"}
            if missing:
                failures.append(row)
        except Exception as exc:
            row = {"index": index, "word": word, "status": "PHONEME_CONVERSION_FAILED", "error": str(exc)}
            failures.append(row)
        rows.append(row)

    result = {
        "status": "PHONE_CONTRACT_CLEAN" if not failures else "PHONE_CONTRACT_REJECTED",
        "word_count": len(words),
        "failed_word_count": len(failures),
        "failures": failures,
        "rows": rows,
        "training_allowed": not failures,
    }
    out = Path(args.output).resolve()
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({k: result[k] for k in ("status", "word_count", "failed_word_count", "training_allowed")}, ensure_ascii=False, indent=2))
    return 0 if not failures else 2


if __name__ == "__main__":
    raise SystemExit(main())
