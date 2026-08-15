class PhonemeDurationEngine:

    VERSION = "1.0.0"

    def analyze(
        self,
        phonemes,
        duration,
    ):

        timeline = []

        if not phonemes:

            return timeline

        part = (
            duration
            / len(
                phonemes
            )
        )

        current = 0.0

        for phoneme in phonemes:

            start = round(
                current,
                2,
            )

            end = round(
                current + part,
                2,
            )

            timeline.append(
                {
                    "phoneme": phoneme,
                    "start": start,
                    "end": end,
                }
            )

            current = end

        return timeline