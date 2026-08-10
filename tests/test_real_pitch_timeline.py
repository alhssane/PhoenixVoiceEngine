"""
Phoenix Voice Studio
Real Pitch Timeline Integration Test

Pipeline:

Audio
    ↓
Pitch Analyzer
    ↓
Pitch Cleanup
    ↓
Musical Note Mapper
    ↓
Pitch Timeline Builder
    ↓
Master Pitch Timeline
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


# ============================================================
# SOURCE AUDIO
# ============================================================

SOURCE = Path(
    r"F:\من بروتوز\مجلد جديد (2)\يامسهره مقطع.wav"
)


# ============================================================
# TEST
# ============================================================

def test_real_pitch_timeline():

    # --------------------------------------------------------
    # Verify audio exists
    # --------------------------------------------------------

    assert SOURCE.exists(), (
        f"Audio file not found:\n{SOURCE}"
    )

    # ========================================================
    # STEP 1
    # PITCH ANALYSIS
    # ========================================================

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
    ), (
        "Pitch analysis returned "
        "an invalid duration."
    )

    assert (
        len(
            pitch_report.frames
        )
        > 0
    ), (
        "Pitch analyzer returned "
        "no frames."
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
    ), (
        "Cleanup received no frames."
    )

    assert (
        cleanup_report.cleaned_frames
        == cleanup_report.original_frames
    ), (
        "Cleanup changed the frame count."
    )

    assert (
        len(
            cleanup_report.frames
        )
        == cleanup_report.cleaned_frames
    ), (
        "Cleanup frame list does not "
        "match cleaned frame count."
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
        len(
            note_timeline.notes
        )
        > 0
    ), (
        "Musical Note Mapper detected "
        "no musical notes."
    )

    assert (
        note_timeline.duration
        > 0
    ), (
        "Musical timeline duration "
        "is invalid."
    )

    # ========================================================
    # STEP 4
    # MASTER PITCH TIMELINE
    # ========================================================

    builder = (
        PitchTimelineBuilder()
    )

    timeline = (
        builder.build(
            cleanup_report,
            note_timeline,
        )
    )

    # ========================================================
    # BASIC TIMELINE VALIDATION
    # ========================================================

    assert (
        timeline.total_frames
        == cleanup_report.cleaned_frames
    ), (
        "Master timeline lost or added "
        "pitch frames."
    )

    assert (
        timeline.duration
        > 0
    ), (
        "Master timeline duration "
        "is invalid."
    )

    assert (
        timeline.total_frames
        > 0
    )

    assert (
        timeline.voiced_frames
        >= 0
    )

    assert (
        timeline.unvoiced_frames
        >= 0
    )

    assert (
        timeline.voiced_frames
        + timeline.unvoiced_frames
        == timeline.total_frames
    ), (
        "Voiced + unvoiced frames do not "
        "equal total frames."
    )

    # ========================================================
    # COVERAGE
    # ========================================================

    assert (
        0
        <= timeline.voiced_coverage
        <= 100
    ), (
        "Invalid voiced coverage."
    )

    assert (
        0
        <= timeline.average_confidence
        <= 100
    ), (
        "Invalid confidence value."
    )

    assert (
        timeline.corrected_frames
        >= 0
    )

    assert (
        0
        <= timeline.correction_coverage
        <= 100
    ), (
        "Invalid correction coverage."
    )

    # ========================================================
    # FRAME VALIDATION
    # ========================================================

    assert (
        len(timeline.frames)
        == timeline.total_frames
    ), (
        "Timeline frame count mismatch."
    )

    voiced_timeline_frames = 0

    for frame in timeline.frames:

        assert (
            frame.index
            >= 0
        )

        assert (
            frame.time
            >= 0
        )

        assert (
            frame.confidence
            >= 0
        )

        assert (
            frame.confidence
            <= 1
        ), (
            "Frame confidence must be "
            "normalized between 0 and 1."
        )

        if frame.voiced:

            assert (
                frame.f0_hz
                > 0
            ), (
                "Voiced frame has invalid F0."
            )

            assert (
                frame.midi
                > 0
            ), (
                "Voiced frame has invalid MIDI."
            )

            assert (
                frame.note_name
                != ""
            ), (
                "Voiced frame has no note name."
            )

            assert (
                frame.octave
                >= 0
            )

            voiced_timeline_frames += 1

        else:

            assert (
                frame.f0_hz
                == 0
            ), (
                "Unvoiced frame contains F0."
            )

    assert (
        voiced_timeline_frames
        == timeline.voiced_frames
    ), (
        "Voiced frame count mismatch."
    )

    # ========================================================
    # CORRECTION VALIDATION
    # ========================================================

    corrected_frames = [
        frame
        for frame in timeline.frames
        if frame.corrected
    ]

    assert (
        len(corrected_frames)
        == timeline.corrected_frames
    ), (
        "Corrected frame count mismatch."
    )

    for frame in corrected_frames:

        assert (
            frame.correction_type
            != ""
        ), (
            "Corrected frame has no "
            "correction type."
        )

    # ========================================================
    # NOTE SEGMENTS
    # ========================================================

    assert (
        len(timeline.segments)
        > 0
    ), (
        "No master timeline segments "
        "were created."
    )

    previous_end = None

    for segment in timeline.segments:

        assert (
            segment.start_time
            >= 0
        )

        assert (
            segment.end_time
            > segment.start_time
        )

        assert (
            segment.duration
            > 0
        )

        assert (
            segment.note_name
            != ""
        )

        assert (
            segment.octave
            >= 0
        )

        assert (
            segment.midi_center
            > 0
        )

        assert (
            segment.f0_center_hz
            > 0
        )

        assert (
            segment.frame_count
            > 0
        )

        assert (
            0
            <= segment.average_confidence
            <= 100
        )

        if previous_end is not None:

            assert (
                segment.start_time
                >= previous_end
            ), (
                "Timeline segments overlap."
            )

        previous_end = (
            segment.end_time
        )

    # ========================================================
    # FRAME → SEGMENT CONSISTENCY
    # ========================================================

    for frame in timeline.frames:

        if not frame.voiced:

            continue

        assert (
            frame.note_index
            is not None
        ), (
            f"Voiced frame at "
            f"{frame.time:.3f}s "
            f"has no musical note."
        )

    return timeline


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":

    print()
    print("=" * 70)
    print(
        "Phoenix Real Pitch Timeline"
    )
    print("=" * 70)

    print()
    print(
        "Loading real audio..."
    )

    timeline = (
        test_real_pitch_timeline()
    )

    print()
    print(
        "## Analysis completed."
    )

    print("-" * 70)

    print(
        f"File                 : "
        f"{timeline.file_name}"
    )

    print(
        f"Duration             : "
        f"{timeline.duration} sec"
    )

    print(
        f"Total Frames         : "
        f"{timeline.total_frames}"
    )

    print(
        f"Voiced Frames        : "
        f"{timeline.voiced_frames}"
    )

    print(
        f"Unvoiced Frames      : "
        f"{timeline.unvoiced_frames}"
    )

    print(
        f"Voiced Coverage      : "
        f"{timeline.voiced_coverage}%"
    )

    print(
        f"Average Confidence   : "
        f"{timeline.average_confidence}%"
    )

    print(
        f"Corrected Frames     : "
        f"{timeline.corrected_frames}"
    )

    print(
        f"Correction Coverage  : "
        f"{timeline.correction_coverage}%"
    )

    print()
    print(
        "## Musical Segments"
    )

    print("-" * 70)

    print(
        f"Total Segments       : "
        f"{len(timeline.segments)}"
    )

    print()

    # --------------------------------------------------------
    # Print first 30 segments only.
    # --------------------------------------------------------

    for segment in timeline.segments[:30]:

        print(
            f"{segment.index:03d}  "
            f"{segment.start_time:8.3f}s -> "
            f"{segment.end_time:8.3f}s  "
            f"{segment.note_name}"
            f"{segment.octave}  "
            f"MIDI: "
            f"{segment.midi_center:7.2f}  "
            f"F0: "
            f"{segment.f0_center_hz:8.2f} Hz  "
            f"Frames: "
            f"{segment.frame_count:4d}  "
            f"Confidence: "
            f"{segment.average_confidence:5.1f}%"
        )

    if len(timeline.segments) > 30:

        print()
        print(
            f"... "
            f"{len(timeline.segments) - 30} "
            f"additional segments not displayed."
        )

    print()
    print(
        "STATUS: PASS"
    )

    print("=" * 70)