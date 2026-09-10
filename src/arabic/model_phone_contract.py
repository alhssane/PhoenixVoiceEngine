from __future__ import annotations

from pathlib import Path
from typing import Iterable


# DiffSinger model families in the current Phoenix pipeline may encode long
# vowels as the corresponding short vowel with duration carrying the length.
# Keep this normalization explicit and centralized rather than duplicating it
# across lyric-rewrite scripts.
MODEL_PHONE_NORMALIZATION: dict[str, str] = {
    "aa": "a",
    "ii": "i",
    "uu": "u",
}


def normalize_model_phone(phone: str) -> str:
    """Map a canonical Phoenix phone to the active baseline representation."""
    value = str(phone).strip()
    return MODEL_PHONE_NORMALIZATION.get(value, value)


def normalize_model_sequence(phones: Iterable[str]) -> tuple[str, ...]:
    """Normalize a phone iterable without dropping phones or changing order."""
    return tuple(normalize_model_phone(phone) for phone in phones if str(phone).strip())


def load_dictionary_phones(path: str | Path) -> frozenset[str]:
    """Load phones from the Phoenix DiffSinger dictionary format.

    The dictionary format is a tab-separated ``name<TAB>phones...`` line.
    Special/runtime phones injected by DiffSinger are intentionally not guessed
    here; callers should validate against the exact active checkpoint contract.
    """
    dictionary_path = Path(path)
    lines = [line.strip() for line in dictionary_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    if not lines:
        raise ValueError(f"Empty phoneme dictionary: {dictionary_path}")

    phones: set[str] = set()
    for line in lines:
        parts = line.split("\t", 1)
        if len(parts) != 2:
            raise ValueError(
                f"Invalid dictionary line (expected tab separator): {line!r}"
            )
        phones.update(parts[1].split())
    return frozenset(phones)


def validate_model_sequence(
    phones: Iterable[str],
    allowed_phones: Iterable[str],
) -> None:
    """Fail closed when a lyric emits a phone outside the active model set."""
    allowed = set(allowed_phones)
    normalized = normalize_model_sequence(phones)
    missing = sorted(set(normalized) - allowed)
    if missing:
        raise ValueError(
            "Phones outside active DiffSinger vocabulary: "
            f"{missing}"
        )
