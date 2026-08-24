from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class SynthesisRequest:
    reference_audio: Path
    melody_audio: Path
    reference_lyrics: str
    target_lyrics: str
    output_audio: Path
    language: str = "ar"
    preserve_style: bool = True
    preserve_melody: bool = True


@dataclass(frozen=True)
class SynthesisResult:
    output_audio: Path
    backend: str
    metadata: dict[str, Any]


class SynthesisBackend(ABC):
    """Stable contract between Phoenix and an actual singing model."""

    name = "abstract"

    @abstractmethod
    def supports(self, language: str) -> bool:
        raise NotImplementedError

    @abstractmethod
    def synthesize(self, request: SynthesisRequest) -> SynthesisResult:
        raise NotImplementedError
