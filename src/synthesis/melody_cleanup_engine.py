import numpy as np


class MelodyCleanupEngine:

    VERSION = "1.0.0"

    def analyze(
        self,
        pitches,
    ):

        cleaned = []

        for pitch in pitches:

            if 80 <= pitch <= 600:

                cleaned.append(
                    pitch
                )

        if not cleaned:

            return []

        return [
            round(
                float(value),
                2,
            )
            for value in cleaned
        ]