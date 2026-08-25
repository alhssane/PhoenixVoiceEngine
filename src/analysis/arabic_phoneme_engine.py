from __future__ import annotations

import re
import shutil
import subprocess
from dataclasses import dataclass


@dataclass(frozen=True)
class PhonemeResult:
    text: str
    phonemes: str
    backend: str


class ArabicPhonemeEngine:
    """Deterministic Arabic G2P front-end for singing synthesis.

    This is deliberately a front-end, not a claim of perfect Arabic
    pronunciation.  It converts normalized Arabic text to IPA-like symbols
    using espeak-ng/espeak when available, while preserving the original text
    for later manual correction and alignment.
    """

    VERSION = "1.0.0"

    def __init__(self, executable: str | None = None) -> None:
        self.executable = executable or shutil.which("espeak-ng") or shutil.which("espeak")

    @staticmethod
    def normalize(text: str) -> str:
        text = text.strip()
        text = re.sub(r"[\u064B-\u065F\u0670]", "", text)
        text = text.replace("ـ", "")
        text = re.sub(r"\s+", " ", text)
        return text

    def phonemize(self, text: str) -> PhonemeResult:
        normalized = self.normalize(text)
        if not normalized:
            raise ValueError("Arabic text cannot be empty")
        if not self.executable:
            raise RuntimeError("Arabic G2P requires espeak-ng or espeak")

        completed = subprocess.run(
            [self.executable, "-q", "--ipa", "-v", "ar", normalized],
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
        )
        if completed.returncode != 0:
            raise RuntimeError(
                "Arabic phonemizer failed: " + completed.stderr.strip()
            )

        phonemes = re.sub(r"\s+", " ", completed.stdout.strip())
        if not phonemes:
            raise RuntimeError("Arabic phonemizer returned no phonemes")
        return PhonemeResult(normalized, phonemes, self.executable)
