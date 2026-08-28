from __future__ import annotations

import importlib.util
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .phoneme_contract import PhoneConversion, ipa_to_canonical, normalize_arabic_for_phonemization


class PhoenixG2PError(RuntimeError):
    """Raised when the Phoenix Arabic G2P frontend cannot produce valid phones."""


@dataclass(frozen=True)
class G2PFrontendResult:
    text: str
    normalized_text: str
    words: tuple[PhoneConversion, ...]
    canonical_phones: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "text": self.text,
            "normalized_text": self.normalized_text,
            "words": [
                {
                    "word": item.word,
                    "ipa": item.ipa,
                    "phones": list(item.phones),
                }
                for item in self.words
            ],
            "canonical_phones": list(self.canonical_phones),
        }


class PhoenixArabicG2PFrontend:
    """
    Production-facing bridge for the real Phoenix Arabic G2P v02 module.

    The frontend deliberately keeps G2P separate from DiffSinger. It converts
    Arabic text -> eSpeak/Phoenix IPA -> the shared Phoenix canonical phone
    contract. It does not mutate any DiffSinger checkpoint or vocabulary.
    """

    def __init__(
        self,
        module_path: str | os.PathLike[str] | None = None,
    ) -> None:
        self.module_path = Path(
            module_path
            or os.environ.get(
                "PHOENIX_ARABIC_G2P_MODULE_PATH",
                r"D:\PhoenixVoiceEngine\external\YingMusic-Singer-Plus\phoenix_arabic_g2p_v02.py",
            )
        )
        self._module: Any | None = None

    def is_available(self) -> bool:
        return self.module_path.is_file()

    def _load(self) -> Any:
        if self._module is not None:
            return self._module
        if not self.is_available():
            raise PhoenixG2PError(f"Phoenix G2P module not found: {self.module_path}")

        spec = importlib.util.spec_from_file_location(
            "phoenix_arabic_g2p_v02_runtime", self.module_path
        )
        if spec is None or spec.loader is None:
            raise PhoenixG2PError(f"Cannot load Phoenix G2P module: {self.module_path}")

        module = importlib.util.module_from_spec(spec)
        try:
            spec.loader.exec_module(module)
        except Exception as exc:  # pragma: no cover - runtime dependency surface
            raise PhoenixG2PError(f"Failed to import Phoenix G2P: {exc}") from exc

        fn = getattr(module, "phonemize_arabic", None)
        if not callable(fn):
            raise PhoenixG2PError(
                "Phoenix G2P v02 must expose callable phonemize_arabic(text)."
            )

        self._module = module
        return module

    def convert_word(self, word: str) -> PhoneConversion:
        module = self._load()
        clean = normalize_arabic_for_phonemization(word)
        if not clean:
            return PhoneConversion(word="", ipa="", phones=())

        try:
            raw = list(module.phonemize_arabic(clean))
        except Exception as exc:  # pragma: no cover - runtime dependency surface
            raise PhoenixG2PError(f"Phoenix G2P failed for {clean!r}: {exc}") from exc

        # The v02 G2P returns normalized phoneme symbols (including long-vowel
        # forms such as aː/iː/uː). Reconstruct the IPA string for traceability,
        # then feed the actual shared Phoenix contract for canonicalization.
        ipa = " ".join(raw)
        try:
            canonical = tuple(ipa_to_canonical(ipa, word=clean))
        except Exception as exc:
            raise PhoenixG2PError(
                f"Phoenix canonicalization failed for {clean!r}: {exc}"
            ) from exc

        return PhoneConversion(
            word=clean,
            ipa=ipa,
            phones=canonical,
        )

    def convert(self, text: str) -> G2PFrontendResult:
        module = self._load()
        _ = module  # explicit load gate
        normalized = normalize_arabic_for_phonemization(text)
        words: list[PhoneConversion] = []
        sequence: list[str] = []

        for raw_word in normalized.split():
            conv = self.convert_word(raw_word)
            if not conv.phones:
                continue
            if sequence:
                sequence.append("|")
            sequence.extend(conv.phones)
            words.append(conv)

        return G2PFrontendResult(
            text=text,
            normalized_text=normalized,
            words=tuple(words),
            canonical_phones=tuple(sequence),
        )
