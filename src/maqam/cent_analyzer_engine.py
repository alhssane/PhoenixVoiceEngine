import math


class CentAnalyzerEngine:

    VERSION = "1.0.0"

    A4 = 440.0

    def hz_to_midi(
        self,
        frequency,
    ):

        if frequency <= 0:

            raise ValueError(
                "Frequency must be greater than zero."
            )

        return (
            69
            + 12
            * math.log2(
                frequency
                / self.A4
            )
        )

    def cents_from_nearest_note(
        self,
        frequency,
    ):

        midi = self.hz_to_midi(
            frequency
        )

        nearest = round(
            midi
        )

        cents = (
            midi
            - nearest
        ) * 100

        return round(
            cents,
            2,
        )

    def analyze(
        self,
        frequency,
    ):

        return {
            "frequency_hz": frequency,
            "cents": self.cents_from_nearest_note(
                frequency
            ),
        }