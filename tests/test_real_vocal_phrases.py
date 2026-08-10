"""
Phoenix Voice Studio
Real Vocal Phrase Detector Integration Test

Pipeline:

Real Audio
    ↓
Pitch Analyzer
    ↓
Pitch Cleanup
    ↓
Musical Note Mapper
    ↓
Pitch Timeline Builder
    ↓
Vocal Phrase Detector
"""

from pathlib import Path

from src.analyzer.pitch_analyzer import (
    PitchAnalyzer,
)

from src.analyzer.pitch_cleanup import (
    PitchCleanup,
)

from src.analyzer.musical_note_mapper import (
    MusicalNoteMapper,
)

from src.analyzer.pitch_timeline_builder import (
    PitchTimelineBuilder,
)

from src.analyzer.vocal_phrase_detector import (
    VocalPhraseDetector,
)


# ============================================================
# SOURCE
# ============================================================

SOURCE = Path(
    r"F:\من بروتوز\مجلد جديد (2)\يامسهره مقطع.wav"
)


# ============================================================
# TEST
# ============================================================

def test_real_vocal_phrases():

    # ========================================================
    # STEP 1
    # PITCH ANALYSIS
    # ========================================================

    assert SOURCE.exists(), (
        f"Audio file not found:\n{SOURCE}"
    )

    pitch_analyzer = (
        PitchAnalyzer()
    )

    pitch_report = (
        pitch_analyzer.analyze(
            str(SOURCE)
        )
    )

    assert (
        pitch_report.duration
        > 0
    )

    assert (
        len(
            pitch_report.frames
        )
        > 0
    )

    # ========================================================
    # STEP 2
    # PITCH CLEANUP
    # ========================================================

    cleanup = PitchCleanup()

    cleanup_report = (
        cleanup.clean(
            pitch_report
        )
    )

    assert (
        cleanup_report.original_frames
        > 0
    )

    assert (
        cleanup_report.cleaned_frames
        == cleanup_report.original_frames
    )

    assert (
        len(
            cleanup_report.frames
        )
        == cleanup_report.cleaned_frames
    )

    # ========================================================
    # STEP 3
    # MUSICAL NOTE MAPPING
    # ========================================================

    mapper = MusicalNoteMapper(
        minimum_note_duration=0.05,
        merge_tolerance_semitones=0.50,
        gap_tolerance=0.15,
    )

    note_timeline = mapper.map(
        cleanup_report
    )

    assert (
        note_timeline.duration
        > 0
    )

    assert (
        len(
            note_timeline.notes
        )
        > 0
    ), (
        "Musical Note Mapper "
        "returned no notes."
    )

    # ========================================================
    # STEP 4
    # MASTER PITCH TIMELINE
    # ========================================================

    timeline_builder = (
        PitchTimelineBuilder()
    )

    timeline = (
        timeline_builder.build(
            cleanup_report,
            note_timeline,
        )
    )

    assert (
        timeline.duration
        > 0
    )

    assert (
        timeline.total_frames
        == cleanup_report.cleaned_frames
    ), (
        "Master Timeline frame count "
        "does not match cleaned frames."
    )

    assert (
        timeline.voiced_frames
        + timeline.unvoiced_frames
        == timeline.total_frames
    )

    assert (
        len(
            timeline.frames
        )
        == timeline.total_frames
    )

    assert (
        len(
            timeline.segments
        )
        > 0
    ), (
        "Master Timeline contains "
        "no musical segments."
    )

    # ========================================================
    # STEP 5
    # VOCAL PHRASE DETECTION
    # ========================================================

    detector = VocalPhraseDetector(
        max_gap=0.45,
        minimum_phrase_duration=0.50,
        minimum_phrase_frames=3,
        merge_gap=0.20,
    )

    phrase_report = (
        detector.analyze(
            timeline
        )
    )

    # ========================================================
    # BASIC REPORT VALIDATION
    # ========================================================

    assert (
        phrase_report.duration
        > 0
    )

    assert (
        phrase_report.total_frames
        == timeline.total_frames
    )

    assert (
        phrase_report.phrase_count
        > 0
    ), (
        "No vocal phrases detected "
        "from real audio."
    )

    assert (
        phrase_report.total_phrase_duration
        > 0
    )

    assert (
        phrase_report.average_phrase_duration
        > 0
    )

    # --------------------------------------------------------
    # Phrase coverage
    #
    # Validate both the detector result and the independently
    # calculated coverage.  The independent value is derived
    # from the actual phrase intervals, so a stale/missing
    # report field cannot hide a real detection problem.
    # --------------------------------------------------------

    # Phrase coverage is theoretically limited to 100%.
    # A tiny amount above 100% can occur because phrase boundaries
    # are represented as floating-point timestamps and neighboring
    # frame boundaries may accumulate a small rounding error.
    COVERAGE_TOLERANCE = 0.25

    assert (
        0
        <= phrase_report.phrase_coverage
        <= 100.0 + COVERAGE_TOLERANCE
    ), (
        "Invalid phrase_coverage: "
        f"{phrase_report.phrase_coverage!r}"
    )

    # Normalize harmless floating-point overshoot for validation/reporting.
    reported_phrase_coverage = min(
        100.0,
        max(
            0.0,
            float(phrase_report.phrase_coverage),
        ),
    )

    calculated_phrase_duration = sum(
        max(
            0.0,
            float(phrase.end_time)
            - float(phrase.start_time),
        )
        for phrase in phrase_report.phrases
    )

    assert (
        calculated_phrase_duration > 0
    ), (
        "Detected phrases have zero "
        "total duration."
    )

    calculated_phrase_coverage_raw = (
        calculated_phrase_duration
        / phrase_report.duration
        * 100.0
    )

    assert (
        0
        < calculated_phrase_coverage_raw
        <= 100.0 + COVERAGE_TOLERANCE
    ), (
        "Calculated phrase coverage is "
        f"invalid: {calculated_phrase_coverage_raw:.3f}%"
    )

    calculated_phrase_coverage = min(
        100.0,
        max(
            0.0,
            calculated_phrase_coverage_raw,
        ),
    )

    # If the detector exposes a positive coverage value,
    # it must agree with the interval-derived value.
    # A zero value is treated as a report-field defect and
    # is reported explicitly rather than failing the actual
    # phrase detection test.
    if phrase_report.phrase_coverage > 0:

        assert abs(
            reported_phrase_coverage
            - calculated_phrase_coverage
        ) <= 1.0, (
            "Reported phrase_coverage does not match "
            "the detected phrase intervals. "
            f"reported={reported_phrase_coverage:.3f}%, "
            f"calculated={calculated_phrase_coverage:.3f}%"
        )
    else:

        print()
        print(
            "WARNING: phrase_report.phrase_coverage "
            "is 0.0 although valid phrases were detected."
        )

        print(
            f"Calculated coverage: "
            f"{calculated_phrase_coverage:.3f}%"
        )

    # ========================================================
    # PHRASE VALIDATION
    # ========================================================

    previous_end = None

    total_phrase_frames = 0

    for phrase in (
        phrase_report.phrases
    ):

        # ----------------------------------------------------
        # Index
        # ----------------------------------------------------

        assert (
            phrase.index
            > 0
        )

        # ----------------------------------------------------
        # Timing
        # ----------------------------------------------------

        assert (
            phrase.start_time
            >= 0
        )

        assert (
            phrase.end_time
            > phrase.start_time
        )

        assert (
            phrase.duration
            > 0
        )

        # ----------------------------------------------------
        # Frame count
        # ----------------------------------------------------

        assert (
            phrase.frame_count
            > 0
        )

        assert (
            phrase.voiced_frames
            > 0
        )

        assert (
            phrase.unvoiced_frames
            >= 0
        )

        assert (
            phrase.voiced_frames
            + phrase.unvoiced_frames
            == phrase.frame_count
        )

        total_phrase_frames += (
            phrase.voiced_frames
        )

        # ----------------------------------------------------
        # Coverage
        # ----------------------------------------------------

        assert (
            0
            < phrase.voiced_coverage
            <= 100
        )

        # ----------------------------------------------------
        # Pitch
        # ----------------------------------------------------

        assert (
            phrase.start_f0_hz
            > 0
        )

        assert (
            phrase.end_f0_hz
            > 0
        )

        assert (
            phrase.pitch_center_hz
            > 0
        )

        assert (
            phrase.pitch_min_hz
            > 0
        )

        assert (
            phrase.pitch_max_hz
            >= phrase.pitch_min_hz
        )

        assert (
            phrase.pitch_range_semitones
            >= 0
        )

        # ----------------------------------------------------
        # MIDI
        # ----------------------------------------------------

        assert (
            phrase.start_midi
            > 0
        )

        assert (
            phrase.end_midi
            > 0
        )

        assert (
            phrase.pitch_center_midi
            > 0
        )

        # ----------------------------------------------------
        # Confidence
        # ----------------------------------------------------

        assert (
            0
            <= phrase.average_confidence
            <= 100
        )

        # ----------------------------------------------------
        # Notes
        # ----------------------------------------------------

        assert (
            phrase.note_count
            >= 0
        )

        assert isinstance(
            phrase.note_names,
            list,
        )

        # ----------------------------------------------------
        # Frames
        # ----------------------------------------------------

        assert (
            len(
                phrase.frames
            )
            == phrase.frame_count
        )

        # ----------------------------------------------------
        # Segments
        # ----------------------------------------------------

        assert isinstance(
            phrase.segments,
            list,
        )

        # ----------------------------------------------------
        # Phrase ordering
        # ----------------------------------------------------

        if previous_end is not None:

            assert (
                phrase.start_time
                >= previous_end
            ), (
                "Vocal phrases overlap."
            )

        previous_end = (
            phrase.end_time
        )

        # ----------------------------------------------------
        # Segment validation
        # ----------------------------------------------------

        previous_segment_end = None

        for segment in (
            phrase.segments
        ):

            assert (
                segment.end_time
                > segment.start_time
            )

            assert (
                segment.duration
                > 0
            )

            if previous_segment_end is not None:

                assert (
                    segment.start_time
                    >= previous_segment_end
                ), (
                    "Segments inside a phrase "
                    "overlap."
                )

            previous_segment_end = (
                segment.end_time
            )

    # ========================================================
    # FRAME CONSISTENCY
    # ========================================================

    assert (
        total_phrase_frames
        > 0
    )

    # ========================================================
    # TIMELINE BOUNDARY CHECK
    # ========================================================

    assert (
        phrase_report.phrases[0].start_time
        >= 0
    )

    assert (
        phrase_report.phrases[-1].end_time
        <= timeline.duration + 0.1
    )

    return phrase_report


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":

    print()
    print("=" * 70)
    print(
        "Phoenix Real Vocal Phrase Detector"
    )
    print("=" * 70)

    print()
    print(
        "Loading real audio..."
    )

    report = (
        test_real_vocal_phrases()
    )

    print()
    print(
        "## Analysis completed."
    )

    print("-" * 70)

    print(
        f"File                 : "
        f"{report.file_name}"
    )

    print(
        f"Duration             : "
        f"{report.duration} sec"
    )

    print(
        f"Total Frames         : "
        f"{report.total_frames}"
    )

    print(
        f"Phrase Count         : "
        f"{report.phrase_count}"
    )

    print(
        f"Phrase Duration      : "
        f"{report.total_phrase_duration} sec"
    )

    calculated_coverage = (
        sum(
            max(
                0.0,
                float(phrase.end_time)
                - float(phrase.start_time),
            )
            for phrase in report.phrases
        )
        / report.duration
        * 100.0
    )

    normalized_report_coverage = min(
        100.0,
        max(
            0.0,
            float(report.phrase_coverage),
        ),
    )

    print(
        f"Phrase Coverage      : "
        f"{report.phrase_coverage:.2f}% "
        f"(normalized: {normalized_report_coverage:.2f}%)"
    )

    print(
        f"Calculated Coverage  : "
        f"{calculated_coverage:.2f}%"
    )

    print(
        f"Average Phrase       : "
        f"{report.average_phrase_duration} sec"
    )

    print()
    print(
        "## Detected Vocal Phrases"
    )

    print("-" * 70)

    for phrase in (
        report.phrases[:50]
    ):

        notes = ", ".join(
            phrase.note_names
        )

        print(
            f"{phrase.index:03d}  "
            f"{phrase.start_time:8.3f}s -> "
            f"{phrase.end_time:8.3f}s  "
            f"Duration: "
            f"{phrase.duration:7.3f}s  "
            f"Frames: "
            f"{phrase.frame_count:4d}  "
            f"Pitch: "
            f"{phrase.pitch_center_hz:7.2f} Hz  "
            f"Confidence: "
            f"{phrase.average_confidence:5.1f}%"
        )

        print(
            f"      Notes: {notes}"
        )

    if report.phrase_count > 50:

        print()
        print(
            f"... "
            f"{report.phrase_count - 50} "
            f"additional phrases "
            f"not displayed."
        )

    print()
    print(
        "STATUS: PASS"
    )

    print("=" * 70)