from dataclasses import dataclass

from src.lyrics.lyrics_replacement_blueprint import (
    LyricsReplacementBlueprint,
)

from src.lyrics.word_replacement_engine import (
    WordReplacementEngine,
)

from src.generation.lyric_melody_generator import (
    LyricMelodyGenerator,
)


@dataclass
class SynthesisResult:

    original_word: str
    replacement_word: str
    maqam: str
    duration: float
    notes: list
    syllable_mapping: dict
    status: str


class RealSingingSynthesisEngine:

    def __init__(self):

        self.blueprint_engine = (
            LyricsReplacementBlueprint()
        )

        self.replacement_engine = (
            WordReplacementEngine()
        )

        self.melody_generator = (
            LyricMelodyGenerator()
        )

    def synthesize(

        self,

        original_word: str,

        replacement_word: str,

        start: float,

        end: float,

        maqam: str,

        ornament: str,

        average_pitch: float,

        quarter_tone: float,

        notes: list,

        syllables: int,

    ):

        blueprint = self.blueprint_engine.build(

            original_word=original_word,
            start=start,
            end=end,
            maqam=maqam,
            ornament=ornament,
            average_pitch=average_pitch,
            quarter_tone=quarter_tone,
            notes=notes,
            syllables=syllables,
        )

        replacement = (
            self.replacement_engine.create_plan(
                blueprint,
                replacement_word,
            )
        )

        melody = (
            self.melody_generator.generate(
                replacement_word,
                blueprint.maqam,
                blueprint.ornament,
                blueprint.duration,
                blueprint.notes,
            )
        )

        return SynthesisResult(

            original_word=replacement.source_word,

            replacement_word=replacement.target_word,

            maqam=replacement.maqam,

            duration=replacement.duration,

            notes=replacement.notes,

            syllable_mapping=melody,

            status="READY",
        )