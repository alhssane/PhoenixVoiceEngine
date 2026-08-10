"""
Phoenix Voice Studio
Lyric Extractor Test Suite

Tests the extractor without requiring a Whisper model
for the synthetic stage.

A real-audio test is included separately and can be run
after faster-whisper is installed.
"""

from dataclasses import dataclass
from pathlib import Path
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


from src.analyzer.lyric_extractor import (
    LyricExtractor,
    LyricExtractionReport,
)


# ============================================================
# MOCK WHISPER OBJECTS
# ============================================================


@dataclass
class MockWord:
    word: str
    start: float
    end: float
    probability: float


@dataclass
class MockSegment:
    start: float
    end: float
    text: str
    avg_logprob: float
    words: list


@dataclass
class MockInfo:
    language: str
    language_probability: float
    duration: float


class MockWhisperModel:

    def transcribe(
        self,
        audio_path,
        **kwargs,
    ):
        assert kwargs["language"] == "ar"
        assert kwargs["task"] == "transcribe"
        assert kwargs["word_timestamps"] is True

        segments = [
            MockSegment(
                start=0.0,
                end=0.8,
                text="يا مسهرة",
                avg_logprob=-0.5,
                words=[
                    MockWord(
                        word="يا",
                        start=0.0,
                        end=0.3,
                        probability=0.95,
                    ),
                    MockWord(
                        word="مسهرة",
                        start=0.3,
                        end=0.8,
                        probability=0.90,
                    ),
                ],
            ),
            MockSegment(
                start=1.0,
                end=1.6,
                text="قلبي معاك",
                avg_logprob=-0.4,
                words=[
                    MockWord(
                        word="قلبي",
                        start=1.0,
                        end=1.3,
                        probability=0.92,
                    ),
                    MockWord(
                        word="معاك",
                        start=1.3,
                        end=1.6,
                        probability=0.91,
                    ),
                ],
            ),
        ]

        info = MockInfo(
            language="ar",
            language_probability=0.98,
            duration=1.6,
        )

        return segments, info


# ============================================================
# TEST
# ============================================================


def test_synthetic_extraction():

    source = Path(
        "synthetic_lyrics.wav"
    )

    source.write_bytes(
        b"synthetic"
    )

    try:
        extractor = LyricExtractor(
            model_size="large-v3",
            language="ar",
            device="cpu",
            compute_type="int8",
        )

        report = extractor.extract(
            str(source),
            model=MockWhisperModel(),
        )

    finally:
        source.unlink(
            missing_ok=True
        )

    assert isinstance(
        report,
        LyricExtractionReport,
    )

    assert (
        report.file_name
        == "synthetic_lyrics.wav"
    )

    assert report.duration == 1.6

    assert report.language == "ar"

    assert (
        report.language_probability
        == 98.0
    )

    assert (
        report.segment_count
        == 2
    )

    assert (
        report.word_count
        == 4
    )

    assert (
        report.text
        == "يا مسهرة قلبي معاك"
    )

    assert (
        0
        < report.average_word_confidence
        <= 100
    )

    assert (
        0
        < report.voiced_coverage
        <= 100
    )

    previous_end = 0.0

    for word in report.words:

        assert word.text

        assert (
            word.start_time
            >= previous_end
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
            0
            <= word.confidence
            <= 100
        )

        previous_end = (
            word.end_time
        )

    for segment in report.segments:

        assert (
            segment.end_time
            >= segment.start_time
        )

        assert (
            segment.duration
            >= 0
        )

        assert segment.text

        for word in segment.words:

            assert (
                word.start_time
                >= segment.start_time
            )

            assert (
                word.end_time
                <= segment.end_time
            )

    data = report.to_dict()

    assert isinstance(
        data,
        dict,
    )

    assert (
        len(data["words"])
        == 4
    )

    return report


# ============================================================
# MAIN
# ============================================================


if __name__ == "__main__":

    print()
    print("=" * 70)
    print("Phoenix Lyric Extractor")
    print("=" * 70)

    print()
    print("TEST 1: Synthetic ASR")
    print("-" * 70)

    report = test_synthetic_extraction()

    print(
        f"File                 : "
        f"{report.file_name}"
    )

    print(
        f"Duration             : "
        f"{report.duration:.3f} sec"
    )

    print(
        f"Language             : "
        f"{report.language}"
    )

    print(
        f"Language Probability : "
        f"{report.language_probability:.1f}%"
    )

    print(
        f"Segments             : "
        f"{report.segment_count}"
    )

    print(
        f"Words                : "
        f"{report.word_count}"
    )

    print(
        f"Average Confidence   : "
        f"{report.average_word_confidence:.1f}%"
    )

    print()
    print("## Extracted Lyrics")
    print("-" * 70)

    for word in report.words:

        print(
            f"{word.index:02d}  "
            f"{word.start_time:7.3f}s -> "
            f"{word.end_time:7.3f}s  "
            f"{word.text:<12} "
            f"Confidence: "
            f"{word.confidence:5.1f}%"
        )

    print()
    print(
        f"Full Text: {report.text}"
    )

    print()
    print("=" * 70)
    print("STATUS: PASS")
    print("=" * 70)