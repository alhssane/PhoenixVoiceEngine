"""
Phoenix Voice Studio
Vocal Candidate Detector
Clean Vocal vs Vocal + Music Test
"""

from pathlib import Path

from src.analyzer.vocal_activity_analyzer import (
    VocalActivityAnalyzer,
)

from src.analyzer.vocal_candidate_detector import (
    VocalCandidateDetector,
)


# ============================================================
# Test files
# ============================================================

CLEAN_VOCAL = Path(
    r"F:\من بروتوز\مجلد جديد (2)\يامسهره مقطع.wav"
)

VOCAL_WITH_MUSIC = Path(
    r"F:\مجلد جديد\ورده البيتت الصغيره.mp3"
)


# ============================================================
# Analyze one file
# ============================================================

def analyze_file(
    audio_path: Path,
):

    print()
    print("=" * 70)
    print(
        f"Analyzing: {audio_path.name}"
    )
    print("=" * 70)

    if not audio_path.exists():

        raise FileNotFoundError(
            f"Audio file not found:\n{audio_path}"
        )

    activity_analyzer = (
        VocalActivityAnalyzer()
    )

    activity_report = (
        activity_analyzer.analyze(
            str(audio_path)
        )
    )

    detector = (
        VocalCandidateDetector()
    )

    report = detector.analyze(
        str(audio_path),
        activity_report.segments,
    )

    print()
    print(
        f"Total Duration       : "
        f"{report.total_duration} sec"
    )

    print(
        f"Candidate Segments   : "
        f"{report.candidate_count}"
    )

    print(
        f"High Confidence      : "
        f"{report.high_confidence_duration} sec"
    )

    print(
        f"Medium/High Duration : "
        f"{report.medium_confidence_duration} sec"
    )

    print(
        f"High Coverage        : "
        f"{report.high_confidence_coverage}%"
    )

    print(
        f"Medium+ Coverage     : "
        f"{report.medium_confidence_coverage}%"
    )

    print()
    print("Segments")
    print("-" * 70)

    for candidate in report.candidates:

        print(
            f"{candidate.index:02d}  "
            f"{candidate.start:08.3f}s -> "
            f"{candidate.end:08.3f}s  "
            f"Confidence: "
            f"{candidate.confidence:5.1f}%  "
            f"{candidate.classification}"
        )

    return report


# ============================================================
# Main
# ============================================================

if __name__ == "__main__":

    print()
    print("=" * 70)
    print("Phoenix Vocal Candidate Comparison")
    print("=" * 70)

    print()
    print("Test 1: Clean Vocal")

    clean_report = analyze_file(
        CLEAN_VOCAL
    )

    print()
    print("Test 2: Vocal + Music")

    music_report = analyze_file(
        VOCAL_WITH_MUSIC
    )

    # ========================================================
    # Comparison
    # ========================================================

    print()
    print("=" * 70)
    print("FINAL COMPARISON")
    print("=" * 70)

    print()

    print(
        f"{'Metric':<25}"
        f"{'Clean Vocal':>20}"
        f"{'Vocal + Music':>20}"
    )

    print("-" * 70)

    print(
        f"{'Duration (sec)':<25}"
        f"{clean_report.total_duration:>20.2f}"
        f"{music_report.total_duration:>20.2f}"
    )

    print(
        f"{'Segments':<25}"
        f"{clean_report.candidate_count:>20}"
        f"{music_report.candidate_count:>20}"
    )

    print(
        f"{'High Confidence (sec)':<25}"
        f"{clean_report.high_confidence_duration:>20.2f}"
        f"{music_report.high_confidence_duration:>20.2f}"
    )

    print(
        f"{'High Coverage (%)':<25}"
        f"{clean_report.high_confidence_coverage:>20.2f}"
        f"{music_report.high_confidence_coverage:>20.2f}"
    )

    print(
        f"{'Medium+ Coverage (%)':<25}"
        f"{clean_report.medium_confidence_coverage:>20.2f}"
        f"{music_report.medium_confidence_coverage:>20.2f}"
    )

    print()

    print("STATUS: PASS")

    print("=" * 70)