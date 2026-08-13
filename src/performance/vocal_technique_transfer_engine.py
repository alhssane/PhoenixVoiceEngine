from typing import Any
from typing import Dict
from typing import List


class VocalTechniqueTransferEngine:

    VERSION = "1.0.0"
    FEATURE_VERSION = "1.0.0"
    PATCH_VERSION = "1.0.0"

    SUPPORTED_TECHNIQUES = (
        "vibrato",
        "trill",
        "glissando",
        "slide",
        "run",
        "melisma",
    )

    def build_technique(
        self,
        technique_type: str,
        start_time: float,
        end_time: float,
        intensity: float,
    ) -> Dict[str, Any]:

        technique_type = str(
            technique_type
        ).lower()

        if (
            technique_type
            not in self.SUPPORTED_TECHNIQUES
        ):

            raise ValueError(
                "Unsupported technique."
            )

        intensity = max(
            0.0,
            min(
                1.0,
                float(intensity),
            ),
        )

        return {
            "type": technique_type,
            "start_time": float(
                start_time
            ),
            "end_time": float(
                end_time
            ),
            "duration": (
                float(end_time)
                - float(start_time)
            ),
            "intensity": intensity,
        }

    def transfer(
        self,
        techniques: List[
            Dict[str, Any]
        ],
        target_words: List[str],
    ) -> List[Dict[str, Any]]:

        transferred = []

        for index, technique in enumerate(
            techniques
        ):

            word = (
                target_words[index]
                if index
                < len(target_words)
                else ""
            )

            transferred.append(
                {
                    "word": word,
                    "technique": technique[
                        "type"
                    ],
                    "start_time": technique[
                        "start_time"
                    ],
                    "end_time": technique[
                        "end_time"
                    ],
                    "intensity": technique[
                        "intensity"
                    ],
                }
            )

        return transferred

    def analyze(
        self,
        techniques: List[
            Dict[str, Any]
        ],
        target_words: List[str],
    ) -> Dict[str, Any]:

        result = self.transfer(
            techniques,
            target_words,
        )

        return {
            "status": "READY",
            "count": len(result),
            "techniques": result,
        }