from __future__ import annotations

from dataclasses import dataclass

from src.arabic.g2p_frontend import PhoenixArabicG2PFrontend
from src.arabic.model_phone_contract import normalize_model_sequence


@dataclass
class SyllableMapping:
    syllable: str
    notes: list


class SyllableNoteMapper:
    """Map Arabic lyric syllables to notes using Phoenix G2P, not letters."""

    def __init__(self, frontend: PhoenixArabicG2PFrontend | None = None) -> None:
        self.frontend = frontend or PhoenixArabicG2PFrontend()

    @staticmethod
    def _syllabify_phones(phones: list[str]) -> list[tuple[str, ...]]:
        seq = list(normalize_model_sequence(phones))
        seq = [p for p in seq if p not in {"|", "SP", "AP"}]
        if not seq:
            return []

        vowels = {"a", "i", "u"}
        vowel_positions = [i for i, phone in enumerate(seq) if phone in vowels]
        if not vowel_positions:
            return [tuple(seq)]

        syllables: list[tuple[str, ...]] = []
        for index, vowel_pos in enumerate(vowel_positions):
            start = 0 if index == 0 else vowel_positions[index - 1] + 1
            end = len(seq) if index == len(vowel_positions) - 1 else vowel_pos + 1
            part = tuple(seq[start:end])
            if part:
                syllables.append(part)
        return syllables

    def split_word(self, word: str) -> list[str]:
        result = self.frontend.convert_word(word)
        syllables = self._syllabify_phones(list(result.phones))
        if not syllables:
            return [word]
        # Keep the actual phone content attached to each syllable. This is much
        # safer than splitting the orthographic Arabic word into characters.
        return [" ".join(syllable) for syllable in syllables]

    def map(self, word: str, notes: list) -> list[SyllableMapping]:
        syllables = self.split_word(word)
        if not notes:
            return []

        if len(notes) < len(syllables):
            raise ValueError(
                f"Not enough notes for lyric syllables: word={word!r}, "
                f"syllables={len(syllables)}, notes={len(notes)}"
            )

        # Deterministically distribute notes, preserving order and assigning at
        # least one note per syllable. Any remaining melisma notes stay on the
        # final syllable until a richer melody-fit stage is introduced.
        base, remainder = divmod(len(notes), len(syllables))
        mappings: list[SyllableMapping] = []
        cursor = 0

        for index, syllable in enumerate(syllables):
            count = base + (1 if index < remainder else 0)
            assigned = notes[cursor:cursor + count]
            cursor += count
            mappings.append(SyllableMapping(syllable=syllable, notes=assigned))

        return mappings
