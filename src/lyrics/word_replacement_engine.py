from dataclasses import dataclass

from src.lyrics.word_duration_mapper import (
    WordDurationMapper
)

from src.lyrics.lyrics_replacement_blueprint import (
    WordBlueprint
)


@dataclass
class ReplacementPlan:
    source_word: str
    target_word: str
    duration: float
    maqam: str
    ornament: str
    compatible: bool
    notes: list


class WordReplacementEngine:

    def __init__(self):

        self.duration_mapper = (
            WordDurationMapper()
        )

    def create_plan(
        self,
        blueprint: WordBlueprint,
        target_word: str
    ):

        mapping = self.duration_mapper.map(
            source_word=blueprint.original_word,
            target_word=target_word,
            source_duration=blueprint.duration
        )

        return ReplacementPlan(
            source_word=blueprint.original_word,
            target_word=target_word,
            duration=blueprint.duration,
            maqam=blueprint.maqam,
            ornament=blueprint.ornament,
            compatible=mapping.compatible,
            notes=blueprint.notes
        )