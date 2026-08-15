import numpy as np


class CrossfadeEngine:

    VERSION = "1.0.0"

    def merge(
        self,
        segments,
        sample_rate=44100,
        fade_ms=80,
    ):

        fade_samples = int(
            sample_rate
            * fade_ms
            / 1000
        )

        output = segments[0]

        for segment in segments[1:]:

            overlap = min(
                fade_samples,
                len(output),
                len(segment),
            )

            fade_out = np.linspace(
                1,
                0,
                overlap,
            )

            fade_in = np.linspace(
                0,
                1,
                overlap,
            )

            mixed = (
                output[-overlap:]
                * fade_out
                +
                segment[:overlap]
                * fade_in
            )

            output = np.concatenate(

                [
                    output[:-overlap],
                    mixed,
                    segment[overlap:],
                ]

            )

        return output