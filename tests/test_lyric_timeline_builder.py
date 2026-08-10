"""
Phoenix Voice Studio
Lyric Timeline Builder Test Suite

Synthetic tests for:
1. Phrase-to-lyric mapping
2. Word timing
3. Note propagation
4. Confidence propagation
5. Timeline coverage
6. Boundary validation
"""

from dataclasses import dataclass, field
from pathlib import Path
import sys


# ============================================================
# PROJECT IMPORT
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


from src.analyzer.lyric_timeline_builder import (
    LyricTimelineBuilder,
    LyricTimelineReport,
    LyricPhrase,
    LyricWord,
)


# ============================================================
# MOCK VOCAL PHRASE
# ============================================================


@dataclass
class MockVocalPhrase:
    index: int

    start_time: float
    end_time: float
    duration: float

    note_names: list = field(
        default_factory=list
    )

    pitch_center_hz: float = 0.0
    pitch_center_midi: float = 0.0

    average_confidence: float = 0.0


@dataclass
class MockVocalPhraseReport:
    file_name: str
    duration: float

    phrases: list = field(
        default_factory=list
    )


# ============================================================
# SYNTHETIC DATA
# ============================================================


def create_synthetic_report():

    phrases = [
        MockVocalPhrase(
            index=1,
            start_time=0.000,
            end_time=0.400,
            duration=0.400,
            note_names=["C4"],
            pitch_center_hz=261.63,
            pitch_center_midi=60.0,
            average_confidence=90.0,
        ),
        MockVocalPhrase(
            index=2,
            start_time=0.500,
            end_time=0.900,
            duration=0.400,
            note_names=["D4"],
            pitch_center_hz=293.66,
            pitch_center_midi=62.0,
            average_confidence=88.0,
        ),
        MockVocalPhrase(
            index=3,
            start_time=1.000,
            end_time=1.600,
            duration=0.600,
            note_names=["E4", "F4"],
            pitch_center_hz=329.63,
            pitch_center_midi=64.0,
            average_confidence=92.0,
        ),
    ]

    return MockVocalPhraseReport(
        file_name="synthetic_lyrics.wav",
        duration=1.600,
        phrases=phrases,
    )


# ============================================================
# BASIC BUILD TEST
# ============================================================


def test_basic_build():

    report = create_synthetic_report()

    lyrics = [
        "يا",
        "مسهرة",
        "قلبي معاك",
    ]

    builder = LyricTimelineBuilder()

    result = builder.build(
        report,
        lyrics=lyrics,
    )

    assert isinstance(
        result,
        LyricTimelineReport,
    )

    assert result.file_name == (
        "synthetic_lyrics.wav"
    )

    assert result.duration == 1.6

    assert result.phrase_count == 3

    assert len(result.phrases) == 3

    return result


# ============================================================
# PHRASE VALIDATION
# ============================================================


def test_phrase_structure(result):

    previous_end = None

    for phrase in result.phrases:

        assert isinstance(
            phrase,
            LyricPhrase,
        )

        assert phrase.start_time >= 0

        assert (
            phrase.end_time
            >= phrase.start_time
        )

        assert (
            phrase.duration
            == round(
                phrase.end_time
                - phrase.start_time,
                6,
            )
        )

        assert (
            phrase.duration
            > 0
        )

        assert phrase.lyric

        assert (
            phrase.pitch_center_hz
            > 0
        )

        assert (
            phrase.pitch_center_midi
            > 0
        )

        assert (
            0
            <= phrase.confidence
            <= 100
        )

        if previous_end is not None:

            assert (
                phrase.start_time
                >= previous_end
            ), (
                "Lyric phrases overlap."
            )

        previous_end = (
            phrase.end_time
        )

    return result


# ============================================================
# WORD TIMING TEST
# ============================================================


def test_word_timing(result):

    for phrase in result.phrases:

        if not phrase.words:
            continue

        previous_end = (
            phrase.start_time
        )

        for word in phrase.words:

            assert isinstance(
                word,
                LyricWord,
            )

            assert word.text

            assert (
                word.start_time
                >= phrase.start_time
            )

            assert (
                word.end_time
                <= phrase.end_time
            )

            assert (
                word.end_time
                >= word.start_time
            )

            assert (
                word.duration
                >= 0
            )

            assert (
                word.start_time
                >= previous_end
            ), (
                "Lyric words overlap."
            )

            assert (
                word.note_names
                == phrase.note_names
            )

            assert (
                0
                <= word.confidence
                <= 100
            )

            previous_end = (
                word.end_time
            )

        # The last word must finish
        # exactly at the phrase boundary.
        assert (
            phrase.words[-1].end_time
            == phrase.end_time
        )

    return result


# ============================================================
# NOTE PROPAGATION TEST
# ============================================================


def test_note_propagation(result):

    expected_notes = [
        ["C4"],
        ["D4"],
        ["E4", "F4"],
    ]

    for phrase, expected in zip(
        result.phrases,
        expected_notes,
    ):

        assert (
            phrase.note_names
            == expected
        )

        for word in phrase.words:

            assert (
                word.note_names
                == expected
            )

    return result


# ============================================================
# CONFIDENCE TEST
# ============================================================


def test_confidence_propagation(result):

    expected = [
        90.0,
        88.0,
        92.0,
    ]

    for phrase, expected_confidence in zip(
        result.phrases,
        expected,
    ):

        assert (
            phrase.confidence
            == expected_confidence
        )

        for word in phrase.words:

            assert (
                word.confidence
                == expected_confidence
            )

    return result


# ============================================================
# COVERAGE TEST
# ============================================================


def test_coverage(result):

    # All three phrases contain lyrics.
    # Their total duration is:
    #
    # 0.4 + 0.4 + 0.6 = 1.4 sec
    #
    # Timeline duration = 1.6 sec
    #
    # Coverage = 87.5%

    assert (
        result.total_lyric_duration
        == 1.4
    )

    assert (
        result.lyric_coverage
        == 87.5
    )

    assert (
        0
        <= result.lyric_coverage
        <= 100
    )

    assert (
        result.average_phrase_duration
        > 0
    )

    return result


# ============================================================
# EMPTY LYRICS TEST
# ============================================================


def test_empty_lyrics():

    report = create_synthetic_report()

    builder = LyricTimelineBuilder()

    result = builder.build(
        report,
        lyrics=[],
    )

    assert (
        result.phrase_count
        == 3
    )

    assert (
        result.total_lyric_duration
        == 0.0
    )

    assert (
        result.lyric_coverage
        == 0.0
    )

    for phrase in result.phrases:

        assert (
            phrase.lyric
            == ""
        )

        assert (
            phrase.words
            == []
        )

    return result


# ============================================================
# MISSING LYRICS TEST
# ============================================================


def test_missing_lyrics():

    report = create_synthetic_report()

    builder = LyricTimelineBuilder()

    result = builder.build(
        report,
        lyrics=[
            "يا",
        ],
    )

    assert (
        result.phrase_count
        == 3
    )

    assert (
        result.phrases[0].lyric
        == "يا"
    )

    assert (
        result.phrases[1].lyric
        == ""
    )

    assert (
        result.phrases[2].lyric
        == ""
    )

    return result


# ============================================================
# BOUNDARY TEST
# ============================================================


def test_boundaries():

    report = create_synthetic_report()

    # Deliberately create a phrase that ends
    # slightly beyond the timeline duration.
    report.phrases[-1].end_time = 1.8

    builder = LyricTimelineBuilder()

    result = builder.build(
        report,
        lyrics=[
            "يا",
            "مسهرة",
            "قلبي معاك",
        ],
    )

    last_phrase = result.phrases[-1]

    assert (
        last_phrase.end_time
        <= result.duration
    )

    assert (
        last_phrase.end_time
        == result.duration
    )

    assert (
        result.lyric_coverage
        <= 100
    )

    return result


# ============================================================
# SERIALIZATION TEST
# ============================================================


def test_serialization(result):

    data = result.to_dict()

    assert isinstance(
        data,
        dict,
    )

    assert (
        data["file_name"]
        == "synthetic_lyrics.wav"
    )

    assert (
        data["phrase_count"]
        == 3
    )

    assert (
        len(data["phrases"])
        == 3
    )

    for phrase in data["phrases"]:

        assert "lyric" in phrase

        assert "words" in phrase

        assert "note_names" in phrase

    return result


# ============================================================
# MAIN TEST RUNNER
# ============================================================


def test_lyric_timeline_builder():

    print()
    print("=" * 70)
    print("Phoenix Lyric Timeline Builder")
    print("=" * 70)

    # --------------------------------------------------------
    # TEST 1
    # --------------------------------------------------------

    print()
    print("TEST 1: Basic Build")
    print("-" * 70)

    result = test_basic_build()

    print(
        f"File                 : "
        f"{result.file_name}"
    )

    print(
        f"Duration             : "
        f"{result.duration:.3f} sec"
    )

    print(
        f"Phrase Count         : "
        f"{result.phrase_count}"
    )

    print(
        f"Lyric Duration       : "
        f"{result.total_lyric_duration:.3f} sec"
    )

    print(
        f"Lyric Coverage       : "
        f"{result.lyric_coverage:.2f}%"
    )

    print(
        f"Average Phrase       : "
        f"{result.average_phrase_duration:.3f} sec"
    )

    # --------------------------------------------------------
    # TEST 2
    # --------------------------------------------------------

    print()
    print("TEST 2: Phrase Structure")
    print("-" * 70)

    test_phrase_structure(result)

    print("PASS")

    # --------------------------------------------------------
    # TEST 3
    # --------------------------------------------------------

    print()
    print("TEST 3: Word Timing")
    print("-" * 70)

    test_word_timing(result)

    print("PASS")

    # --------------------------------------------------------
    # TEST 4
    # --------------------------------------------------------

    print()
    print("TEST 4: Note Propagation")
    print("-" * 70)

    test_note_propagation(result)

    print("PASS")

    # --------------------------------------------------------
    # TEST 5
    # --------------------------------------------------------

    print()
    print("TEST 5: Confidence Propagation")
    print("-" * 70)

    test_confidence_propagation(result)

    print("PASS")

    # --------------------------------------------------------
    # TEST 6
    # --------------------------------------------------------

    print()
    print("TEST 6: Coverage")
    print("-" * 70)

    test_coverage(result)

    print("PASS")

    # --------------------------------------------------------
    # TEST 7
    # --------------------------------------------------------

    print()
    print("TEST 7: Empty Lyrics")
    print("-" * 70)

    test_empty_lyrics()

    print("PASS")

    # --------------------------------------------------------
    # TEST 8
    # --------------------------------------------------------

    print()
    print("TEST 8: Missing Lyrics")
    print("-" * 70)

    test_missing_lyrics()

    print("PASS")

    # --------------------------------------------------------
    # TEST 9
    # --------------------------------------------------------

    print()
    print("TEST 9: Boundary Protection")
    print("-" * 70)

    test_boundaries()

    print("PASS")

    # --------------------------------------------------------
    # TEST 10
    # --------------------------------------------------------

    print()
    print("TEST 10: Serialization")
    print("-" * 70)

    test_serialization(result)

    print("PASS")

    # --------------------------------------------------------
    # SAMPLE TIMELINE
    # --------------------------------------------------------

    print()
    print("## Lyric Timeline")
    print("-" * 70)

    for phrase in result.phrases:

        print(
            f"{phrase.index:02d}  "
            f"{phrase.start_time:7.3f}s -> "
            f"{phrase.end_time:7.3f}s  "
            f"{phrase.lyric:<15} "
            f"Pitch: "
            f"{phrase.pitch_center_hz:7.2f} Hz  "
            f"Notes: "
            f"{', '.join(phrase.note_names)}"
        )

        for word in phrase.words:

            print(
                f"      "
                f"{word.start_time:7.3f}s -> "
                f"{word.end_time:7.3f}s  "
                f"{word.text:<12} "
                f"Confidence: "
                f"{word.confidence:5.1f}%"
            )

    print()
    print("=" * 70)
    print("STATUS: PASS")
    print("=" * 70)

    return result


if __name__ == "__main__":
    test_lyric_timeline_builder()