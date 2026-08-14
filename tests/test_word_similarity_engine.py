from src.lyrics.word_similarity_engine import (
    WordSimilarityEngine
)


def test_build():

    engine = WordSimilarityEngine()

    result = engine.compare(
        "فريدة",
        "ترانيم"
    )

    assert result.score > 0


def run():

    print()
    print("PhoenixVoiceEngine")
    print("Word Similarity Engine V1.0")
    print("=" * 60)

    print("TEST 1: test_build - ", end="")

    test_build()

    print("PASS")
    print()

    engine = WordSimilarityEngine()

    result = engine.compare(
        "فريدة",
        "ترانيم"
    )

    print("Word Comparison")
    print("=" * 40)

    print(f"Source: {result.source_word}")
    print(f"Target: {result.target_word}")

    print(f"Source letters: {result.source_length}")
    print(f"Target letters: {result.target_length}")

    print(f"Source syllables: {result.source_syllables}")
    print(f"Target syllables: {result.target_syllables}")

    print(f"Similarity: {result.score}%")

    print()
    print("STATUS: PASS")


if __name__ == "__main__":
    run()