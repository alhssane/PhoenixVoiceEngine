"""
Phoenix Voice Studio
Real Lyric Extractor Test

Runs the real faster-whisper ASR engine against the
reference Arabic vocal recording.

Reference audio:
F:\من بروتوز\مجلد جديد (2)\يامسهره مقطع.wav
"""

from pathlib import Path
import json
import sys
import time


# ============================================================
# PROJECT ROOT
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


from src.analyzer.lyric_extractor import (
    LyricExtractor,
    LyricExtractionReport,
)


# ============================================================
# CONFIGURATION
# ============================================================

SOURCE = Path(
    r"F:\مجلد جديد\كلمات جديده بصوت بندر.wav"
)

OUTPUT = (
    PROJECT_ROOT
    / "outputs"
    / "lyrics"
    / "bender_lyrics.json"
)

MODEL_SIZE = "large-v3"

LANGUAGE = "ar"

DEVICE = "cuda"

COMPUTE_TYPE = "float16"

MAX_WORDS_TO_PRINT = 100


# ============================================================
# VALIDATION
# ============================================================


def validate_report(
    report: LyricExtractionReport,
):

    assert report.duration > 0, (
        "Invalid audio duration."
    )

    assert report.file_name, (
        "Missing file name."
    )

    assert report.language == LANGUAGE, (
        f"Expected language '{LANGUAGE}', "
        f"got '{report.language}'."
    )

    assert (
        0
        <= report.language_probability
        <= 100
    ), (
        "Invalid language probability."
    )

    assert report.segment_count >= 0

    assert report.word_count >= 0

    assert (
        0
        <= report.average_word_confidence
        <= 100
    ), (
        "Invalid average word confidence."
    )

    assert (
        0
        <= report.voiced_coverage
        <= 100
    ), (
        "Invalid voiced coverage."
    )

    # --------------------------------------------------------
    # SEGMENTS
    # --------------------------------------------------------

    previous_segment_end = 0.0

    for segment in report.segments:

        assert (
            segment.start_time
            >= 0
        ), (
            "Segment starts before zero."
        )

        assert (
            segment.end_time
            >= segment.start_time
        ), (
            "Invalid segment timing."
        )

        assert (
            segment.end_time
            <= report.duration + 0.05
        ), (
            "Segment exceeds audio duration."
        )

        assert (
            segment.start_time
            >= previous_segment_end - 0.001
        ), (
            "Segments overlap."
        )

        assert segment.duration >= 0

        assert (
            0
            <= segment.confidence
            <= 100
        )

        previous_segment_end = (
            segment.end_time
        )

        # ----------------------------------------------------
        # WORDS INSIDE SEGMENT
        # ----------------------------------------------------

        previous_word_end = (
            segment.start_time
        )

        for word in segment.words:

            assert word.text.strip(), (
                "Empty word detected."
            )

            assert (
                word.start_time
                >= segment.start_time - 0.001
            ), (
                "Word starts before its segment."
            )

            assert (
                word.end_time
                <= segment.end_time + 0.001
            ), (
                "Word ends after its segment."
            )

            assert (
                word.end_time
                >= word.start_time
            ), (
                "Invalid word timing."
            )

            assert (
                word.duration >= 0
            )

            assert (
                word.start_time
                >= previous_word_end - 0.001
            ), (
                "Words overlap inside a segment."
            )

            assert (
                0
                <= word.confidence
                <= 100
            )

            previous_word_end = (
                word.end_time
            )

    # --------------------------------------------------------
    # GLOBAL WORD TIMELINE
    # --------------------------------------------------------

    previous_word_end = 0.0

    for word in report.words:

        assert word.text.strip(), (
            "Empty word detected."
        )

        assert (
            word.start_time
            >= 0
        ), (
            "Word starts before zero."
        )

        assert (
            word.end_time
            >= word.start_time
        ), (
            "Invalid word timing."
        )

        assert (
            word.end_time
            <= report.duration + 0.05
        ), (
            "Word exceeds audio duration."
        )

        assert (
            word.start_time
            >= previous_word_end - 0.001
        ), (
            "Global word timeline contains overlap."
        )

        assert (
            0
            <= word.confidence
            <= 100
        )

        previous_word_end = (
            word.end_time
        )

    assert (
        report.word_count
        == len(report.words)
    )

    assert (
        report.segment_count
        == len(report.segments)
    )


# ============================================================
# SAVE JSON
# ============================================================


def save_report(
    report: LyricExtractionReport,
):

    OUTPUT.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    OUTPUT.write_text(
        json.dumps(
            report.to_dict(),
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )


# ============================================================
# MAIN TEST
# ============================================================


def test_real_lyric_extractor():

    assert SOURCE.exists(), (
        "Audio file not found:\n"
        f"{SOURCE}"
    )

    assert SOURCE.is_file(), (
        "Audio source is not a file:\n"
        f"{SOURCE}"
    )

    print()
    print("=" * 70)
    print("Phoenix Real Lyric Extractor")
    print("=" * 70)

    print()
    print("Loading real audio...")
    print(
        f"File: {SOURCE.name}"
    )

    print()
    print(
        f"Model      : {MODEL_SIZE}"
    )

    print(
        f"Language   : {LANGUAGE}"
    )

    print(
        f"Device     : {DEVICE}"
    )

    print(
        f"Compute    : {COMPUTE_TYPE}"
    )

    print()
    print(
        "Loading faster-whisper model..."
    )

    started = time.perf_counter()

    extractor = LyricExtractor(
        model_size=MODEL_SIZE,
        language=LANGUAGE,
        device=DEVICE,
        compute_type=COMPUTE_TYPE,
        beam_size=5,
        vad_filter=True,
        min_silence_duration_ms=500,
    )

    report = extractor.extract(
        str(SOURCE)
    )

    elapsed = (
        time.perf_counter()
        - started
    )

    print()
    print("## Analysis completed.")
    print("-" * 70)

    print(
        f"Duration             : "
        f"{report.duration:.2f} sec"
    )

    print(
        f"Language             : "
        f"{report.language}"
    )

    print(
        f"Language Probability : "
        f"{report.language_probability:.2f}%"
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
        f"{report.average_word_confidence:.2f}%"
    )

    print(
        f"Coverage             : "
        f"{report.voiced_coverage:.2f}%"
    )

    print(
        f"Processing Time      : "
        f"{elapsed:.2f} sec"
    )

    # ========================================================
    # TEXT
    # ========================================================

    print()
    print("## Extracted Lyrics")
    print("-" * 70)

    if report.text:
        print(report.text)
    else:
        print(
            "[NO LYRICS DETECTED]"
        )

    # ========================================================
    # WORD TIMELINE
    # ========================================================

    print()
    print(
        f"## Word Timeline "
        f"(first {MAX_WORDS_TO_PRINT})"
    )
    print("-" * 70)

    for word in report.words[
        :MAX_WORDS_TO_PRINT
    ]:

        print(
            f"{word.index:04d}  "
            f"{word.start_time:8.3f}s -> "
            f"{word.end_time:8.3f}s  "
            f"{word.text:<20} "
            f"Confidence: "
            f"{word.confidence:5.1f}%"
        )

    if (
        len(report.words)
        > MAX_WORDS_TO_PRINT
    ):

        print()
        print(
            f"... "
            f"{len(report.words) - MAX_WORDS_TO_PRINT} "
            f"additional words not displayed."
        )

    # ========================================================
    # VALIDATION
    # ========================================================

    print()
    print("## Validation")
    print("-" * 70)

    validate_report(report)

    print(
        "Timeline validation   : PASS"
    )

    # ========================================================
    # SAVE
    # ========================================================

    save_report(report)

    print()
    print(
        f"JSON saved            : "
        f"{OUTPUT}"
    )

    # ========================================================
    # FINAL
    # ========================================================

    print()
    print("=" * 70)
    print("STATUS: PASS")
    print("=" * 70)

    return report


if __name__ == "__main__":
    test_real_lyric_extractor()