import librosa


class MelodyConditioningEngine:

    VERSION = "1.0.0"

    def analyze(
        self,
        audio_file,
        start_time,
        end_time,
    ):

        audio, sr = librosa.load(
            audio_file,
            sr=None,
        )

        start_sample = int(
            start_time
            * sr
        )

        end_sample = int(
            end_time
            * sr
        )

        segment = audio[
            start_sample:end_sample
        ]

        pitches, _ = librosa.piptrack(
            y=segment,
            sr=sr,
        )

        values = []

        for frame in range(
            pitches.shape[1]
        ):

            pitch = pitches[
                :,
                frame,
            ].max()

            if pitch > 0:

                values.append(
                    round(
                        float(
                            pitch
                        ),
                        2,
                    )
                )

        return values