"""
Phoenix Voice Studio
Musical Note Mapper Test
"""

from dataclasses import dataclass

from src.analyzer.musical_note_mapper import (
    MusicalNoteMapper,
)


@dataclass
class MockFrame:

    time: float
    f0: float
    confidence: float
    voiced: bool = True
    corrected: bool = False


@dataclass
class MockCleanupReport:

    file_name: str
    duration: float
    frames: list


def create_test_report():

    frequencies = [
        261.63,
        261.63,
        261.63,
        261.63,

        293.66,
        293.66,
        293.66,
        293.66,

        329.63,
        329.63,
        329.63,
        329.63,

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
        file_name="synthetic_notes.wav",
        duration=1.60,
        frames=frames,
    )


def test_musical_note_mapper():

    report = (
        create_test_report()
    )

    mapper = (
        MusicalNoteMapper(
            minimum_note_duration=0.05,
            merge_tolerance_semitones=0.50,
            gap_tolerance=0.15,
        )
    )

    timeline = mapper.map(
        report
    )

    assert (
        timeline.total_notes
        == 4
    )

    assert (
        timeline.duration
        > 0
    )

    assert (
        timeline.voiced_duration
        > 0
    )

    assert (
        0
        <= timeline.voiced_coverage
        <= 100
    )

    assert (
        timeline.pitch_min_midi
        > 0
    )

    assert (
        timeline.pitch_max_midi
        > 0
    )

    assert (
        timeline.average_confidence
        > 0
    )

    expected_notes = [
        "C",
        "D",
        "E",
        "D",
    ]

    for note, expected in zip(
        timeline.notes,
        expected_notes,
    ):

        assert (
            note.note_name
            == expected
        )

        assert (
            note.duration
            > 0
        )

        assert (
            note.frequency_hz
            > 0
        )

        assert (
            0
            <= note.confidence
            <= 100
        )

    return timeline


if __name__ == "__main__":

    print()
    print("=" * 70)
    print(
        "Phoenix Musical Note Mapper"
    )
    print("=" * 70)

    timeline = (
        test_musical_note_mapper()
    )

    print()
    print(
        "Analysis completed."
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
        f"Total Notes          : "
        f"{timeline.total_notes}"
    )

    print(
        f"Voiced Duration      : "
        f"{timeline.voiced_duration} sec"
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
        f"Pitch Minimum        : "
        f"{timeline.pitch_min_midi} MIDI"
    )

    print(
        f"Pitch Maximum        : "
        f"{timeline.pitch_max_midi} MIDI"
    )

    print(
        f"Pitch Center         : "
        f"{timeline.pitch_center_midi} MIDI"
    )

    print()
    print(
        "## Musical Timeline"
    )

    print("-" * 70)

    for note in timeline.notes:

        print(
            f"{note.index:02d}  "
            f"{note.start_time:8.3f}s -> "
            f"{note.end_time:8.3f}s  "
            f"{note.note_name}{note.octave:<3} "
            f"MIDI: {note.midi:6.2f}  "
            f"F0: {note.frequency_hz:7.2f} Hz  "
            f"Duration: {note.duration:6.3f}s  "
            f"Confidence: "
            f"{note.confidence:5.1f}%"
        )

    print()
    print(
        "STATUS: PASS"
    )

    print("=" * 70)