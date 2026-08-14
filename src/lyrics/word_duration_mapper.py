from dataclasses import dataclass


@dataclass
class DurationMappingResult:
    source_word: str
    target_word: str
    source_duration: float
    target_duration: float
    ratio: float
    compatible: bool


class WordDurationMapper:

    def estimate_duration(self, word):

        letters = len(word)

        duration = letters * 0.06

        return round(duration, 2)

    def map(
        self,
        source_word,
        target_word,
        source_duration
    ):

        target_duration = self.estimate_duration(
            target_word
        )

        ratio = round(
            target_duration / source_duration,
            2
        )

        compatible = (
            0.7 <= ratio <= 1.3
        )

        return DurationMappingResult(
            source_word=source_word,
            target_word=target_word,
            source_duration=source_duration,
            target_duration=target_duration,
            ratio=ratio,
            compatible=compatible
        )