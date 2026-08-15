import json
from pathlib import Path

import numpy as np
import soundfile as sf


class WordReconstructionEngine:

    VERSION = "1.0.0"

    def analyze(
        self,
        phoneme_directory,
        replacement_word,
        duration,
        sample_rate=44100,
    ):

        phoneme_path = Path(
            phoneme_directory
        )

        segments = []

        for letter in replacement_word:

            candidates = list(
                phoneme_path.glob(
                    f"*_{letter}.wav"
                )
            )

            if candidates:

                audio, sr = sf.read(
                    candidates[0]
                )

                segments.append(
                    audio
                )

        if not segments:

            return None

        generated = np.concatenate(
            segments
        )

        target_samples = int(
            duration
            * sample_rate
        )

        generated = np.interp(
            np.linspace(
                0,
                len(generated) - 1,
                target_samples,
            ),
            np.arange(
                len(generated)
            ),
            generated,
        )

        output = (
            Path(
                r"D:\PhoenixVoiceEngine\outputs"
            )
            / "generated_farah.wav"
        )

        sf.write(
            output,
            generated,
            sample_rate,
        )

        metadata = {
            "word": replacement_word,
            "duration": duration,
            "output": str(
                output
            ),
        }

        with open(
            output.with_suffix(
                ".json"
            ),
            "w",
            encoding="utf-8",
        ) as file:

            json.dump(
                metadata,
                file,
                ensure_ascii=False,
                indent=4,
            )

        return metadata