from dataclasses import dataclass


@dataclass
class SimilarityResult:
    source_word: str
    target_word: str
    source_length: int
    target_length: int
    source_syllables: int
    target_syllables: int
    score: float


class WordSimilarityEngine:

    def estimate_syllables(self, word):

        count = 0

        vowels = "اويaeiouAEIOU"

        for letter in word:

            if letter in vowels:
                count += 1

        return max(1, count)

    def compare(self, source_word, target_word):

        source_length = len(source_word)
        target_length = len(target_word)

        source_syllables = self.estimate_syllables(source_word)
        target_syllables = self.estimate_syllables(target_word)

        length_score = (
            min(source_length, target_length)
            / max(source_length, target_length)
        )

        syllable_score = (
            min(source_syllables, target_syllables)
            / max(source_syllables, target_syllables)
        )

        score = round(
            ((length_score + syllable_score) / 2) * 100,
            2
        )

        return SimilarityResult(
            source_word=source_word,
            target_word=target_word,
            source_length=source_length,
            target_length=target_length,
            source_syllables=source_syllables,
            target_syllables=target_syllables,
            score=score
        )