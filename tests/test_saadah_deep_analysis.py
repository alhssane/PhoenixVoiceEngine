import json
from pathlib import Path

from src.analysis.real_note_extraction_engine import (
    RealNoteExtractionEngine,
)

WORD_FILE = (
    r"D:\PhoenixVoiceEngine\workspace\replacement_segments\saadah.wav"
)

print()
print("PhoenixVoiceEngine")
print("Saadah Deep Analysis V1.0")
print("=" * 60)

notes = (
    RealNoteExtractionEngine()
    .analyze(
        WORD_FILE
    )
)

result = {
    "word": "سعادة",
    "replacement": "فرح",
    "duration": 0.94,
    "notes": notes,
}

output = Path(
    r"D:\PhoenixVoiceEngine\workspace\replacement_segments\saadah_analysis.json"
)

output.write_text(
    json.dumps(
        result,
        ensure_ascii=False,
        indent=4,
    ),
    encoding="utf-8",
)

print()

print("Analysis")

print("=" * 40)

print(
    json.dumps(
        result,
        ensure_ascii=False,
        indent=4,
    )
)

print()

print(
    f"Saved: {output}"
)

print()

print("STATUS: PASS")