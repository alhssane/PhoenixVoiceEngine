"""
Phoenix Voice Studio
Vocal Phrase Detector Test
"""

from dataclasses import dataclass

from src.analyzer.vocal_phrase_detector import (
    VocalPhraseDetector,
)


# ============================================================
# MOCK FRAME
# ============================================================


@dataclass
class MockFrame:

    time: float
    f0_hz: float
    confidence: float
    voiced: bool = True
    midi: float = 60.0
    note_name: str = "C"
    octave: int = 4


@dataclass
class MockSegment:

    index: int
    start_time: float
    end_time: float
    note_name: str
    octave: int
    midi_center: float
    f0_center_hz: float


@dataclass
class MockTimeline:

    file_name: str
    duration: float
    frames: list
    segments: list


# ============================================================
# CREATE SYNTHETIC TIMELINE
# ============================================================


def create_test_timeline():

    frames = []

    # --------------------------------------------------------
    # Phrase 1
    # 0.000 → 1.000
    # --------------------------------------------------------

    for index in range(10):

        frames.append(
            MockFrame(
                time=index * 0.1,
                f0_hz=261.63,
                confidence=0.90,
                midi=60.0,
                note_name="C",
                octave=4,
            )
        )

    # --------------------------------------------------------
    # Phrase 2
    # 1.500 → 2.500
    #
    # 0.500 second silence/gap.
    # --------------------------------------------------------

    for index in range(10):

        frames.append(
            MockFrame(
                time=1.5 + index * 0.1,
                f0_hz=293.66,
                confidence=0.90,
                midi=62.0,
                note_name="D",
                octave=4,
            )
        )

    segments = [
        MockSegment(
            index=1,
            start_time=0.0,
            end_time=1.0,
            note_name="C",
            octave=4,
            midi_center=60.0,
            f0_center_hz=261.63,
        ),
        MockSegment(
            index=2,
            start_time=1.5,
            end_time=2.5,
            note_name="D",
            octave=4,
            midi_center=62.0,
            f0_center_hz=293.66,
        ),
    ]

    return MockTimeline(
        file_name="synthetic_phrases.wav",
        duration=2.5,
        frames=frames,
        segments=segments,
    )


# ============================================================
# TEST
# ============================================================


def test_vocal_phrase_detector():

    timeline = (
        create_test_timeline()
    )

    detector = VocalPhraseDetector(
        max_gap=0.45,
        minimum_phrase_duration=0.50,
        minimum_phrase_frames=3,
        merge_gap=0.20,
    )

    report = detector.analyze(
        timeline
    )

    # --------------------------------------------------------
    # Basic report
    # --------------------------------------------------------

    assert (
        report.duration
        == 2.5
    )

    assert (
        report.total_frames
        == 20
    )

    assert (
        report.phrase_count
        == 2
    )

    assert (
        report.total_phrase_duration
        > 0
    )

    assert (
        0
        < report.phrase_coverage
        <= 100
    )

    # --------------------------------------------------------
    # Phrase 1
    # --------------------------------------------------------

    phrase1 = (
        report.phrases[0]
    )

    assert (
        phrase1.index
        == 1
    )

    assert (
        abs(
            phrase1.start_time
            - 0.0
        )
        < 0.001
    )

    assert (
        abs(
            phrase1.end_time
            - 1.0
        )
        < 0.001
    )

    assert (
        phrase1.voiced_frames
        == 10
    )

    assert (
        phrase1.note_count
        == 1
    )

    assert (
        "C4"
        in phrase1.note_names
    )

    # --------------------------------------------------------
    # Phrase 2
    # --------------------------------------------------------

    phrase2 = (
        report.phrases[1]
    )

    assert (
        phrase2.index
        == 2
    )

    assert (
        abs(
            phrase2.start_time
            - 1.5
        )
        < 0.001
    )

    assert (
        abs(
            phrase2.end_time
            - 2.5
        )
        < 0.001
    )

    assert (
        phrase2.voiced_frames
        == 10
    )

    assert (
        phrase2.note_count
        == 1
    )

    assert (
        "D4"
        in phrase2.note_names
    )

    # --------------------------------------------------------
    # Phrase order
    # --------------------------------------------------------

    for first, second in zip(
        report.phrases,
        report.phrases[1:],
    ):

        assert (
            first.end_time
            <= second.start_time
        )

    return report


# ============================================================
# MAIN
# ============================================================


if __name__ == "__main__":

    print()
    print("=" * 70)
    print(
        "Phoenix Vocal Phrase Detector"
    )
    print("=" * 70)

    print()
    print(
        "Loading synthetic phrase data..."
    )

    report = (
        test_vocal_phrase_detector()
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

    print(
        f"Phrase Coverage      : "
        f"{report.phrase_coverage}%"
    )

    print(
        f"Average Phrase       : "
        f"{report.average_phrase_duration} sec"
    )

    print()
    print(
        "## Vocal Phrases"
    )

    print("-" * 70)

    for phrase in report.phrases:

        print(
            f"{phrase.index:02d}  "
            f"{phrase.start_time:7.3f}s -> "
            f"{phrase.end_time:7.3f}s  "
            f"Duration: "
            f"{phrase.duration:6.3f}s  "
            f"Frames: "
            f"{phrase.frame_count:3d}  "
            f"Pitch: "
            f"{phrase.pitch_center_hz:7.2f} Hz  "
            f"Confidence: "
            f"{phrase.average_confidence:5.1f}%"
        )

        print(
            f"    Notes: "
            f"{', '.join(phrase.note_names)}"
        )

    print()
    print(
        "STATUS: PASS"
    )

    print("=" * 70)