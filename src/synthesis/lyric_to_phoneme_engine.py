from __future__ import annotations

from src.arabic.g2p_frontend import PhoenixArabicG2PFrontend


class LyricToPhonemeEngine:
    """Convert Arabic lyric text to Phoenix canonical phonemes.

    The previous implementation split a word into Arabic characters. That is
    not a phoneme representation and cannot distinguish sounds such as long
    vowels, emphatics, or digraphs. Production lyric conversion must use the
    shared Phoenix Arabic G2P contract.
    """

    VERSION = "2.0.0"

    def __init__(self, frontend: PhoenixArabicG2PFrontend | None = None) -> None:
        self.frontend = frontend or PhoenixArabicG2PFrontend()

    def analyze(self, word: str) -> list[str]:
        result = self.frontend.convert_word(word)
        return list(result.phones)
