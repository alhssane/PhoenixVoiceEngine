from dataclasses import dataclass
from typing import List


@dataclass
class WordBlueprint:
    original_word: str
    start: float
    end: float
    duration: float
    maqam: str
    ornament: str
    average_pitch: float
    quarter_tone: float
    notes: List[str]
    syllables: int


class LyricsReplacementBlueprint:

    def build(
        self,
        original_word: str,
        start: float,
        end: float,
        maqam: str,
        ornament: str,
        average_pitch: float,
        quarter_tone: float,
        notes: List[str],
        syllables: int
    ):

        duration = round(end - start, 2)

        return WordBlueprint(
            original_word=original_word,
            start=start,
            end=end,
            duration=duration,
            maqam=maqam,
            ornament=ornament,
            average_pitch=average_pitch,
            quarter_tone=quarter_tone,
            notes=notes,
            syllables=syllables
        )