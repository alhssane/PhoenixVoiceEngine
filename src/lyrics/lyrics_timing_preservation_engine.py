from typing import Any
from typing import Dict
from typing import List


class LyricsTimingPreservationEngine:

    VERSION = "1.0.0"
    FEATURE_VERSION = "1.0.0"
    PATCH_VERSION = "1.0.0"

    def build_word_timing(
        self,
        word: str,
        start_time: float,
        end_time: float,
    ) -> Dict[str, Any]:

        return {
            "word": str(word),
            "start_time": float(start_time),
            "end_time": float(end_time),
            "duration": float(end_time) - float(start_time),
        }

    def preserve_timing(
        self,
        original_timeline: List[Dict[str, Any]],
        replacement_words: List[str],
    ) -> List[Dict[str, Any]]:

        timeline = []

        for index, original in enumerate(original_timeline):

            replacement = (
                replacement_words[index]
                if index < len(replacement_words)
                else ""
            )

            timeline.append(
                {
                    "position": index,
                    "original_word": original["word"],
                    "replacement_word": replacement,
                    "start_time": original["start_time"],
                    "end_time": original["end_time"],
                    "duration": original["duration"],
                }
            )

        return timeline

    def analyze(
        self,
        original_timeline: List[Dict[str, Any]],
        replacement_words: List[str],
    ) -> Dict[str, Any]:

        timeline = self.preserve_timing(
            original_timeline,
            replacement_words,
        )

        return {
            "status": "READY",
            "count": len(timeline),
            "timeline": timeline,
        }