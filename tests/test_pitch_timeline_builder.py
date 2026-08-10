"""
Phoenix Voice Studio
Pitch Timeline Builder Test
"""

from dataclasses import dataclass

from src.analyzer.musical_note_mapper import (
    MusicalNoteMapper,
)

from src.analyzer.pitch_timeline_builder import (
    PitchTimelineBuilder,
)


# ============================================================
# MOCK FRAME
# ============================================================


@dataclass
class MockFrame:

    time: float
    f0: float
    confidence: float
    voiced: bool = True
    corrected: bool = False
    correction_type: str = ""


@dataclass
class MockCleanupReport:

    file_name: str
    duration: float
    frames: list


# ============================================================
# CREATE SYNTHETIC CLEANUP REPORT
# ============================================================


def create_cleanup_report():

    frequencies = [

        # C4
        261.63,
        261.63,
        261.63,
        261.63,

        # D4
        293.66,
        293.66,
        293.66,
        293.66,

        # E4
        329.63,
        329.63,
        329.63,
        329.63,

        # D4
        293.66,
        293.66,
        293.66,
        293.66,
    ]

    frames = []

    for index, frequency in enumerate(
        frequencies
    ):

        frames.append(
            MockFrame(
                time=index * 0.10,
                f0=frequency,
                confidence=0.90,
                voiced=True,
            )
        )

    return MockCleanupReport(
        file_name="synthetic_timeline.wav",
        duration=1.60,
        frames=frames,
    )


# ============================================================
# TEST
# ============================================================


def test_pitch_timeline_builder():

    cleanup_report = (
        create_cleanup_report()
    )

    # --------------------------------------------------------
    # Musical Note Mapper
    #
    # The gap tolerance is intentionally larger than the
    # synthetic 0.10 second frame spacing.
    # --------------------------------------------------------

    mapper = MusicalNoteMapper(
        minimum_note_duration=0.05,
        merge_tolerance_semitones=0.50,
        gap_tolerance=0.15,
    )

    note_timeline = mapper.map(
        cleanup_report
    )

    assert (
        len(note_timeline.notes)
        == 4
    ), (
        "Expected exactly 4 musical notes."
    )

    # --------------------------------------------------------
    # Build master pitch timeline
    # --------------------------------------------------------

    builder = (
        PitchTimelineBuilder()
    )

    timeline = builder.build(
        cleanup_report,
        note_timeline,
    )

    # ========================================================
    # BASIC STATISTICS
    # ========================================================

    assert (
        timeline.total_frames
        == 16
    ), (
        "Expected 16 pitch frames."
    )

    assert (
        timeline.voiced_frames
        == 16
    ), (
        "Expected all 16 frames to be voiced."
    )

    assert (
        timeline.unvoiced_frames
        == 0
    ), (
        "Expected zero unvoiced frames."
    )

    assert (
        abs(
            timeline.voiced_coverage
            - 100.0
        )
        < 0.001
    ), (
        "Voiced coverage should be 100%."
    )

    assert (
        abs(
            timeline.average_confidence
            - 90.0
        )
        < 0.001
    ), (
        "Average confidence should be 90%."
    )

    assert (
        timeline.corrected_frames
        == 0
    ), (
        "Synthetic test should contain no corrections."
    )

    assert (
        abs(
            timeline.correction_coverage
        )
        < 0.001
    ), (
        "Correction coverage should be 0%."
    )

    # ========================================================
    # FRAME TIMELINE
    # ========================================================

    assert (
        len(timeline.frames)
        == 16
    ), (
        "Master timeline must contain all pitch frames."
    )

    # --------------------------------------------------------
    # First frame
    # --------------------------------------------------------

    first = timeline.frames[0]

    assert (
        first.note_name
        == "C"
    ), (
        f"First frame should be C, got {first.note_name}"
    )

    assert (
        first.octave
        == 4
    ), (
        f"First frame should be octave 4, got {first.octave}"
    )

    assert (
        abs(
            first.midi
            - 60.0
        )
        < 0.01
    ), (
        f"Expected MIDI 60, got {first.midi}"
    )

    assert (
        abs(
            first.f0_hz
            - 261.63
        )
        < 0.01
    ), (
        f"Expected 261.63 Hz, got {first.f0_hz}"
    )

    # ========================================================
    # NOTE ASSOCIATION
    # ========================================================

    # We intentionally do NOT assume whether the mapper uses
    # zero-based or one-based note indices.
    #
    # What matters is that adjacent musical regions receive
    # different note indices and that the boundary belongs to
    # the new note.

    first_note_index = (
        timeline.frames[0].note_index
    )

    second_note_index = (
        timeline.frames[4].note_index
    )

    third_note_index = (
        timeline.frames[8].note_index
    )

    fourth_note_index = (
        timeline.frames[12].note_index
    )

    assert (
        first_note_index is not None
    ), (
        "First frame was not assigned to a note."
    )

    assert (
        second_note_index is not None
    ), (
        "Second note region was not assigned."
    )

    assert (
        third_note_index is not None
    ), (
        "Third note region was not assigned."
    )

    assert (
        fourth_note_index is not None
    ), (
        "Fourth note region was not assigned."
    )

    assert (
        len(
            {
                first_note_index,
                second_note_index,
                third_note_index,
                fourth_note_index,
            }
        )
        == 4
    ), (
        "The four musical regions must have "
        "four distinct note indices."
    )

    # ========================================================
    # BOUNDARY TEST
    # ========================================================

    # 0.400 is the boundary between C4 and D4.
    #
    # The frame at 0.400 must belong to D4,
    # not C4.

    boundary_frame = (
        timeline.frames[4]
    )

    assert (
        boundary_frame.note_name
        == "D"
    ), (
        "Boundary frame at 0.400s must belong to D4."
    )

    assert (
        boundary_frame.octave
        == 4
    ), (
        "Boundary frame must be octave 4."
    )

    assert (
        abs(
            boundary_frame.midi
            - 62.0
        )
        < 0.01
    ), (
        "Boundary frame must have MIDI 62."
    )

    # ========================================================
    # MUSICAL NOTE REGIONS
    # ========================================================

    expected_notes = [
        "C",
        "D",
        "E",
        "D",
    ]

    expected_midi = [
        60.0,
        62.0,
        64.0,
        62.0,
    ]

    assert (
        len(timeline.segments)
        == 4
    ), (
        "Expected exactly 4 timeline segments."
    )

    for (
        segment,
        expected_note,
        expected_midi_value,
    ) in zip(
        timeline.segments,
        expected_notes,
        expected_midi,
    ):

        assert (
            segment.note_name
            == expected_note
        ), (
            f"Expected {expected_note}, "
            f"got {segment.note_name}"
        )

        assert (
            segment.octave
            == 4
        ), (
            f"{expected_note} should be octave 4."
        )

        assert (
            abs(
                segment.midi_center
                - expected_midi_value
            )
            < 0.01
        ), (
            f"Expected MIDI "
            f"{expected_midi_value}, "
            f"got {segment.midi_center}"
        )

        assert (
            segment.frame_count
            == 4
        ), (
            f"{expected_note} should contain "
            f"4 frames."
        )

        assert (
            abs(
                segment.duration
                - 0.4
            )
            < 0.001
        ), (
            f"{expected_note} duration "
            f"should be 0.4 seconds."
        )

        assert (
            abs(
                segment.average_confidence
                - 90.0
            )
            < 0.001
        ), (
            f"{expected_note} confidence "
            f"should be 90%."
        )

    # ========================================================
    # SEGMENT ORDER
    # ========================================================

    for index in range(
        len(timeline.segments) - 1
    ):

        current = (
            timeline.segments[index]
        )

        next_segment = (
            timeline.segments[index + 1]
        )

        assert (
            current.end_time
            <= next_segment.start_time
        ), (
            "Timeline segments must not overlap."
        )

    return timeline


# ============================================================
# MAIN
# ============================================================


if __name__ == "__main__":

    print()
    print("=" * 70)
    print(
        "Phoenix Pitch Timeline Builder"
    )
    print("=" * 70)

    print()
    print(
        "Loading synthetic pitch data..."
    )

    timeline = (
        test_pitch_timeline_builder()
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
        "## Master Pitch Timeline"
    )

    print("-" * 70)

    for segment in timeline.segments:

        print(
            f"{segment.index:02d}  "
            f"{segment.start_time:7.3f}s -> "
            f"{segment.end_time:7.3f}s  "
            f"{segment.note_name}"
            f"{segment.octave}  "
            f"MIDI: "
            f"{segment.midi_center:6.2f}  "
            f"F0: "
            f"{segment.f0_center_hz:8.2f} Hz  "
            f"Frames: "
            f"{segment.frame_count:3d}  "
            f"Confidence: "
            f"{segment.average_confidence:5.1f}%"
        )

    print()
    print(
        "STATUS: PASS"
    )

    print("=" * 70)