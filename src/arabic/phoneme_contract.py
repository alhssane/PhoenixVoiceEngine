from __future__ import annotations

"""Canonical Arabic phoneme contract for PhoenixVoiceEngine.

This module defines one normalized symbol inventory and conservative aliases so
all Arabic-to-phoneme stages use the same symbols before dictionary/token IDs
are assigned.  It intentionally does not guess linguistic content; it only
normalizes equivalent spellings and validates membership in the project
inventory.
"""

from dataclasses import dataclass
from typing import Iterable

# Canonical symbols already used by the Phoenix DiffSinger dictionary.
CANONICAL_PHONEMES: tuple[str, ...] = (
    "<", "D", "H", "S", "T", "^",
    "a", "b", "d", "f", "g", "h", "i", "k", "l", "m", "n",
    "q", "r", "s", "sh", "t", "th", "u", "x", "z",
)

# Conservative aliases produced by Arabic transliteration systems.  The
# aliases map to canonical Phoenix symbols; they do not invent new phones.
ALIASES: dict[str, str] = {
    "ʃ": "sh",
    "š": "sh",
    "ch": "sh",
    "θ": "th",
    "þ": "th",
    "ð": "D",
    "dh": "D",
    "ʕ": "^",
    "ʿ": "^",
    "ع": "^",
    "ħ": "H",
    "ḥ": "H",
    "ح": "H",
    "ṣ": "S",
    "ص": "S",
    "ṭ": "T",
    "ط": "T",
    "ḍ": "D",
    "ض": "D",
    "ẓ": "D",
    "ظ": "D",
    "ġ": "x",
    "ɣ": "x",
    "غ": "x",
    "kh": "x",
    "خ": "x",
}

# Common stress/length markers should be removed rather than treated as
# independent acoustic phones unless a dataset explicitly defines them.
DROP_MARKERS = {"ː", ":", "'", "`", "ˈ", "ˌ"}


@dataclass(frozen=True)
class PhonemeValidation:
    original: tuple[str, ...]
    normalized: tuple[str, ...]
    unknown: tuple[str, ...]

    @property
    def ok(self) -> bool:
        return not self.unknown


def normalize_phoneme(symbol: str) -> str:
    s = str(symbol).strip()
    if not s:
        return ""
    if s in DROP_MARKERS:
        return ""
    if s in ALIASES:
        return ALIASES[s]
    # Normalize simple multi-character aliases before single-symbol lookup.
    low = s.lower()
    if low in ALIASES:
        return ALIASES[low]
    return s


def normalize_sequence(symbols: Iterable[str]) -> PhonemeValidation:
    original = tuple(str(x) for x in symbols)
    normalized: list[str] = []
    unknown: list[str] = []
    for raw in original:
        value = normalize_phoneme(raw)
        if not value:
            continue
        if value not in CANONICAL_PHONEMES:
            unknown.append(value)
        else:
            normalized.append(value)
    return PhonemeValidation(original, tuple(normalized), tuple(sorted(set(unknown))))


def assert_valid_sequence(symbols: Iterable[str], *, context: str = "phoneme sequence") -> tuple[str, ...]:
    result = normalize_sequence(symbols)
    if not result.ok:
        raise ValueError(
            f"{context} contains unknown phonemes: {', '.join(result.unknown)}"
        )
    return result.normalized
