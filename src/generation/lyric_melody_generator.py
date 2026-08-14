from dataclasses import dataclass

from src.generation.syllable_note_mapper import (
    SyllableNoteMapper
)


@dataclass
class GeneratedLyric:

    word: str
    maqam: str
    ornament: str
    duration: float
    structure: list


class LyricMelodyGenerator:

    def __init__(self):

        self.mapper = SyllableNoteMapper()

    def generate(
        self,
        word,
        maqam,
        ornament,
        duration,
        notes
    ):

        mapping = self.mapper.map(
            word,
            notes
        )

        structure = []

        for item in mapping:

            structure.append(
                {
                    "syllable": item.syllable,
                    "notes": item.notes
                }
            )

        return GeneratedLyric(
            word=word,
            maqam=maqam,
            ornament=ornament,
            duration=duration,
            structure=structure
        )