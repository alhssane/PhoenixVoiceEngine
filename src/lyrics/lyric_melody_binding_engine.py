from typing import Any
from typing import Dict
from typing import List


class LyricMelodyBindingEngine:

    VERSION = "1.0.0"
    FEATURE_VERSION = "1.0.0"
    PATCH_VERSION = "1.0.0"

    def build_note(
        self,
        pitch: str,
        start_time: float,
        end_time: float,
    ) -> Dict[str, Any]:

        return {
            "pitch": str(pitch),
            "start_time": float(start_time),
            "end_time": float(end_time),
            "duration": float(end_time) - float(start_time),
        }

    def bind(
        self,
        words: List[str],
        melody: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:

        bindings = []

        for index, note in enumerate(melody):

            word = (
                words[index]
                if index < len(words)
                else ""
            )

            bindings.append(
                {
                    "position": index,
                    "word": word,
                    "pitch": note["pitch"],
                    "start_time": note["start_time"],
                    "end_time": note["end_time"],
                }
            )

        return bindings

    def analyze(
        self,
        words: List[str],
        melody: List[Dict[str, Any]],
    ) -> Dict[str, Any]:

        bindings = self.bind(
            words,
            melody,
        )

        return {
            "status": "READY",
            "count": len(bindings),
            "bindings": bindings,
        }