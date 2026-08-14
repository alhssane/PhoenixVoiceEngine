from collections import Counter

from src.maqam.quarter_tone_map_engine import (
    QuarterToneMapEngine,
)


class QuarterToneProfileEngine:

    VERSION = "1.0.0"

    def build_profile(
        self,
        file_path,
    ):

        analyzer = (
            QuarterToneMapEngine()
        )

        results = analyzer.analyze(
            file_path
        )

        counter = Counter()

        for item in results:

            note = item["note"]

            counter[note] += 1

        total = sum(
            counter.values()
        )

        profile = {}

        if total == 0:

            return profile

        for note, count in counter.items():

            profile[note] = round(
                count
                / total
                * 100,
                2,
            )

        return dict(
            sorted(
                profile.items(),
                key=lambda item: item[1],
                reverse=True,
            )
        )