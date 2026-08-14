from dataclasses import dataclass
from typing import List


@dataclass
class MelodyTemplate:

    source_word: str
    maqam: str
    ornament: str
    duration: float
    notes: List[str]
    note_count: int


class MelodyTemplateEngine:

    def build(
        self,
        source_word,
        maqam,
        ornament,
        duration,
        notes
    ):

        return MelodyTemplate(
            source_word=source_word,
            maqam=maqam,
            ornament=ornament,
            duration=duration,
            notes=notes,
            note_count=len(notes)
        )