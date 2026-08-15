import librosa
import numpy as np


class BreathDetectionEngine:

    VERSION = "1.0.0"

    def detect(
        self,
        audio_path,
        frame_length=2048,
        hop_length=512,
        silence_threshold=0.20,
        minimum_pause=0.15,
    ):

        audio, sample_rate = librosa.load(
            audio_path,
            sr=None,
            mono=True,
        )

        rms = librosa.feature.rms(
            y=audio,
            frame_length=frame_length,
            hop_length=hop_length,
        )[0]

        rms = rms / np.max(rms)

        times = librosa.frames_to_time(
            np.arange(len(rms)),
            sr=sample_rate,
            hop_length=hop_length,
        )

        pauses = []

        pause_start = None

        for time, energy in zip(
            times,
            rms,
        ):

            if energy < silence_threshold:

                if pause_start is None:

                    pause_start = time

            else:

                if pause_start is not None:

                    duration = (
                        time - pause_start
                    )

                    if (
                        duration
                        >= minimum_pause
                    ):

                        pauses.append(
                            {
                                "start": round(
                                    pause_start,
                                    2,
                                ),
                                "end": round(
                                    time,
                                    2,
                                ),
                                "duration": round(
                                    duration,
                                    2,
                                ),
                            }
                        )

                    pause_start = None

        return pauses