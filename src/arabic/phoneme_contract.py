from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Any

# Canonical phones used by Phoenix Arabic SVS. The set intentionally includes
# the full consonant inventory emitted by Epitran plus long vowels and word
# boundaries. Stage6 derives the final DiffSinger dictionary from observed
# canonical phones, so adding a valid phone here is architecture-safe for new
# training runs.
CANONICAL_PHONES = {
    "<", "^", "S", "D", "T", "Z",
    "a", "aa", "b", "d", "f", "g", "h", "H", "i", "ii", "j", "k",
    "l", "m", "n", "q", "r", "s", "sh", "t", "th", "u", "uu", "w", "x", "y", "z",
    "|",
}

# Epitran Arabic IPA -> Phoenix canonical phones.
IPA_MULTI_MAP = {
    "sˤ": "S",
    "dˤ": "D",
    "tˤ": "T",
    "zˤ": "Z",
    "t͡ʃ": "sh",
    "d͡ʒ": "j",
}

IPA_CHAR_MAP = {
    "ʔ": "<",
    "b": "b", "t": "t", "d": "d", "k": "k", "q": "q",
    "f": "f", "s": "s", "z": "z",
    "ʃ": "sh", "ʒ": "j",
    "x": "x", "χ": "x", "ɣ": "g", "ɢ": "g",
    "θ": "th", "ð": "th",
    "ħ": "H", "ʕ": "^",
    "h": "h", "m": "m", "n": "n", "r": "r", "ɾ": "r",
    "l": "l", "w": "w", "j": "y",
    "a": "a", "i": "i", "u": "u",
    "e": "a", "o": "u",
}

_ARABIC_DIACRITICS = re.compile(r"[\u064b-\u065f\u0670\u06d6-\u06ed]")
_PUNCT = set(",.!?؛،:;()[]{}'\"`“”‘’…")


class UnsupportedArabicPhone(ValueError):
    pass


@dataclass(frozen=True)
class PhoneConversion:
    word: str
    ipa: str
    phones: tuple[str, ...]


def normalize_arabic_for_phonemization(text: str) -> str:
    text = str(text or "").strip()
    _ARABIC_DIACRITICS.sub("", text)
    text = _ARABIC_DIACRITICS.sub("", text)
    text = text.replace("ـ", "")
    # Orthographic forms that Epitran leaves literal. For singing lyrics,
    # final ta-marbuta is normally sung as the open /a/ sound, while medial
    # ta-marbuta behaves as /t/; alif-maqsura is the /a/ vowel.
    text = text.replace("ى", "ا")
    text = re.sub(r"ة(?=\s|$)", "ا", text)
    text = text.replace("ؤ", "و").replace("ئ", "ي")
    text = re.sub(r"\s+", " ", text)
    return text


def ipa_to_canonical(ipa: str, *, word: str = "") -> list[str]:
    tokens: list[str] = []
    i = 0
    while i < len(ipa):
        ch = ipa[i]
        if ch.isspace() or ch in _PUNCT:
            i += 1
            continue

        matched = False
        for seq, mapped in sorted(IPA_MULTI_MAP.items(), key=lambda kv: len(kv[0]), reverse=True):
            if ipa.startswith(seq, i):
                tokens.append(mapped)
                i += len(seq)
                matched = True
                break
        if matched:
            continue

        if ch == "ː":
            if not tokens:
                raise UnsupportedArabicPhone(f"Length mark without a preceding phone: word={word!r}, ipa={ipa!r}")
            prev = tokens[-1]
            if prev in {"a", "i", "u"}:
                tokens[-1] = prev + prev
            else:
                # Epitran may attach length to a consonant in edge cases.
                # Preserve the audible consonant as a second phone rather
                # than silently deleting the mark.
                tokens.append(prev)
            i += 1
            continue

        mapped = IPA_CHAR_MAP.get(ch)
        if mapped is None:
            # Combining tie/secondary marks are meaningful only when they
            # were already consumed by a multi-IPA sequence.
            if ch in {"͡", "ˤ", "̩", "̆"}:
                i += 1
                continue
            raise UnsupportedArabicPhone(
                f"Unsupported IPA symbol {ch!r}: word={word!r}, ipa={ipa!r}, index={i}"
            )
        tokens.append(mapped)
        i += 1

    invalid = [p for p in tokens if p not in CANONICAL_PHONES - {"|"}]
    if invalid:
        raise UnsupportedArabicPhone(f"Invalid canonical phones {invalid!r}: word={word!r}, ipa={ipa!r}")
    return tokens


def phonemize_arabic_word(epi: Any, word: str) -> PhoneConversion:
    clean = normalize_arabic_for_phonemization(word)
    if not clean:
        return PhoneConversion(word=clean, ipa="", phones=())
    ipa = epi.transliterate(clean, normpunc=True)
    phones = ipa_to_canonical(ipa, word=clean)
    return PhoneConversion(word=clean, ipa=ipa, phones=tuple(phones))


def phonemize_arabic_text(epi: Any, text: str) -> list[str]:
    output: list[str] = []
    for raw_word in str(text or "").split():
        conv = phonemize_arabic_word(epi, raw_word)
        if not conv.phones:
            continue
        if output:
            output.append("|")
        output.extend(conv.phones)
    return output


def validate_phone_sequence(phones: list[str], *, allowed: set[str] | None = None) -> None:
    allowed_set = allowed if allowed is not None else CANONICAL_PHONES
    bad = [p for p in phones if p not in allowed_set]
    if bad:
        raise UnsupportedArabicPhone(f"Unsupported canonical phones: {sorted(set(bad))}")
