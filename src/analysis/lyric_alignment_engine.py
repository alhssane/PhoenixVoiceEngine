from src.analysis.syllable_detection_engine import (
    SyllableDetectionEngine,
)

from src.analysis.frame_tracking_engine import (
    FrameTrackingEngine,
)

from src.maqam.segmented_pyin_maqam_detector import (
    SegmentedPyinMaqamDetector,
)


class LyricAlignmentEngine:

    VERSION = "1.0.0"

    def analyze(
        self,
        file_path,
    ):

        syllables = (
            SyllableDetectionEngine()
            .analyze(file_path)
        )

        frames = (
            FrameTrackingEngine()
            .analyze(file_path)
        )

        maqams = (
            SegmentedPyinMaqamDetector()
            .analyze(file_path)
        )

        results = []

        for syllable in syllables:

            start = syllable["start"]

            end = syllable["end"]

            notes = []

            for frame in frames:

                if (
                    start
                    <= frame["time"]
                    <= end
                ):

                    notes.append(
                        frame["note"]
                    )

            maqam_name = "unknown"

            for maqam in maqams:

                if (
                    maqam["start"]
                    <= start
                    <= maqam["end"]
                ):

                    maqam_name = (
                        maqam["maqam"]
                    )

                    break

            results.append(
                {
                    "start": start,
                    "end": end,
                    "duration": syllable[
                        "duration"
                    ],
                    "notes": notes,
                    "maqam": maqam_name,
                }
            )

        return results