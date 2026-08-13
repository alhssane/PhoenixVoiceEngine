from typing import Any, Dict, List


class LyricsReplacementEngine:

    VERSION = "1.0.0"
    FEATURE_VERSION = "1.0.0"
    PATCH_VERSION = "1.0.0"

    def tokenize(
        self,
        text: str,
    ) -> List[str]:

        return text.strip().split()

    def build_mapping(
        self,
        original_lyrics: str,
        new_lyrics: str,
    ) -> List[Dict[str, Any]]:

        original_tokens = self.tokenize(
            original_lyrics,
        )

        new_tokens = self.tokenize(
            new_lyrics,
        )

        maximum = max(
            len(original_tokens),
            len(new_tokens),
        )

        mapping = []

        for index in range(maximum):

            original_word = (
                original_tokens[index]
                if index < len(original_tokens)
                else None
            )

            new_word = (
                new_tokens[index]
                if index < len(new_tokens)
                else None
            )

            mapping.append(
                {
                    "position": index,
                    "original": original_word,
                    "replacement": new_word,
                }
            )

        return mapping

    def analyze(
        self,
        original_lyrics: str,
        new_lyrics: str,
    ) -> Dict[str, Any]:

        mapping = self.build_mapping(
            original_lyrics,
            new_lyrics,
        )

        return {
            "status": "READY",
            "original_word_count": len(
                self.tokenize(
                    original_lyrics,
                )
            ),
            "replacement_word_count": len(
                self.tokenize(
                    new_lyrics,
                )
            ),
            "mapping": mapping,
        }