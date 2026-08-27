from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any


MODEL = "gemini-3.5-transcribe"


def _get_attr(obj: Any, name: str, default: Any = None) -> Any:
    if isinstance(obj, dict):
        return obj.get(name, default)
    return getattr(obj, name, default)


def _time_to_seconds(value: Any) -> float | None:
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    text = str(value).strip()
    if not text:
        return None
    if text.endswith("ms"):
        return float(text[:-2]) / 1000.0
    if text.endswith("s"):
        return float(text[:-1])
    # Accept simple MM:SS(.mmm) as a defensive fallback.
    if ":" in text:
        parts = text.split(":")
        if len(parts) == 2:
            return float(parts[0]) * 60.0 + float(parts[1])
    match = re.fullmatch(r"([0-9]+(?:\.[0-9]+)?)", text)
    if match:
        return float(match.group(1))
    return None


def _jsonable(value: Any) -> Any:
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, list):
        return [_jsonable(x) for x in value]
    if isinstance(value, tuple):
        return [_jsonable(x) for x in value]
    if isinstance(value, dict):
        return {str(k): _jsonable(v) for k, v in value.items()}
    model_dump = getattr(value, "model_dump", None)
    if callable(model_dump):
        try:
            return _jsonable(model_dump(mode="json"))
        except Exception:
            pass
    to_dict = getattr(value, "to_dict", None)
    if callable(to_dict):
        try:
            return _jsonable(to_dict())
        except Exception:
            pass
    if hasattr(value, "__dict__"):
        return {
            str(k): _jsonable(v)
            for k, v in vars(value).items()
            if not str(k).startswith("_")
        }
    return str(value)


def extract_word_annotations(interaction: Any) -> list[dict[str, Any]]:
    words: list[dict[str, Any]] = []
    for step in _get_attr(interaction, "steps", []) or []:
        for content in _get_attr(step, "content", []) or []:
            for annotation in _get_attr(content, "annotations", []) or []:
                if _get_attr(annotation, "type") != "word_info":
                    continue
                text = (_get_attr(annotation, "text", "") or "").strip()
                start = _time_to_seconds(_get_attr(annotation, "start_offset"))
                end = _time_to_seconds(_get_attr(annotation, "end_offset"))
                if not text or start is None or end is None:
                    continue
                words.append(
                    {
                        "word": text,
                        "start": start,
                        "end": end,
                        "duration": end - start,
                        "source": "gemini-3.5-transcribe",
                    }
                )
    words.sort(key=lambda item: (item["start"], item["end"]))
    return words


def transcribe_audio(
    audio_path: str | Path,
    output_path: str | Path,
    language_codes: list[str] | None = None,
    custom_vocabulary: list[str] | None = None,
    raw_output_path: str | Path | None = None,
) -> dict[str, Any]:
    try:
        from google import genai
    except ImportError as exc:
        raise RuntimeError(
            "google-genai is not installed. Install requirements-gemini.txt first."
        ) from exc

    path = Path(audio_path).resolve()
    output = Path(output_path).resolve()
    if not path.exists():
        raise FileNotFoundError(f"Audio file not found: {path}")

    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise RuntimeError(
            "GEMINI_API_KEY (or GOOGLE_API_KEY) is not set in the environment."
        )

    try:
        import soundfile as sf

        info = sf.info(str(path))
        audio_duration = info.duration
        sample_rate = info.samplerate
        channels = info.channels
    except Exception as exc:
        raise RuntimeError(f"Unable to inspect audio: {path}") from exc

    client = genai.Client(api_key=api_key)
    try:
        uploaded = client.files.upload(file=str(path))
        generation_config: dict[str, Any] = {
            "transcription_config": {
                "language_codes": language_codes or [],
                "mode": {
                    "type": "verbatim",
                    "timestamp_granularities": ["word"],
                },
            }
        }
        if custom_vocabulary:
            generation_config["transcription_config"]["custom_vocabulary"] = list(
                custom_vocabulary[:1000]
            )

        interaction = client.interactions.create(
            model=MODEL,
            input=[
                {
                    "type": "audio",
                    "uri": uploaded.uri,
                    "mime_type": uploaded.mime_type,
                }
            ],
            generation_config=generation_config,
        )

        words = extract_word_annotations(interaction)
        transcript_text = _get_attr(interaction, "output_text", "") or ""

        invalid: list[dict[str, Any]] = []
        previous_end = -1.0
        for index, item in enumerate(words):
            start = item["start"]
            end = item["end"]
            if end <= start:
                invalid.append({"index": index, "reason": "non_positive_duration", "word": item["word"]})
            if start < previous_end - 1e-6:
                invalid.append({"index": index, "reason": "overlap_or_unsorted", "word": item["word"]})
            if end > audio_duration + 0.25:
                invalid.append({"index": index, "reason": "beyond_audio_duration", "word": item["word"]})
            previous_end = max(previous_end, end)

        words_valid = not invalid and bool(words)
        result = {
            "schema_version": "phoenix-gemini-transcript-v1",
            "status": "GEMINI_TRANSCRIPTION_READY" if words_valid else "GEMINI_TRANSCRIPTION_REJECTED",
            "model": MODEL,
            "audio": {
                "path": str(path),
                "duration_sec": audio_duration,
                "sample_rate": sample_rate,
                "channels": channels,
            },
            "language_codes": language_codes or [],
            "word_count": len(words),
            "transcript_text": transcript_text,
            "words": words,
            "validation": {
                "word_annotations_present": bool(words),
                "invalid_word_count": len(invalid),
                "invalid_words": invalid,
                "last_word_end_sec": max((w["end"] for w in words), default=0.0),
            },
            "training_allowed": False,
            "next_gate": "PHOENIX_TRANSCRIPT_VALIDATION_AND_COVERAGE",
        }

        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")

        if raw_output_path:
            raw_path = Path(raw_output_path).resolve()
            raw_path.parent.mkdir(parents=True, exist_ok=True)
            raw_path.write_text(
                json.dumps(_jsonable(interaction), ensure_ascii=False, indent=2),
                encoding="utf-8",
            )

        if not words_valid:
            raise RuntimeError(
                "Gemini returned no valid word-level timestamps; see the output report."
            )
        return result
    finally:
        close = getattr(client, "close", None)
        if callable(close):
            close()
