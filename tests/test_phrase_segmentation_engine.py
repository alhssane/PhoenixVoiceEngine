import json
import os

from src.segmentation.phrase_segmentation_engine import (
    PhraseSegmentationEngine,
)


print()
print("PhoenixVoiceEngine")
print(
    "Phrase Segmentation Engine V2"
)
print("=" * 60)
print()

engine = (
    PhraseSegmentationEngine()
)

database = engine.segment(
    audio_path=r"F:\مجلد جديد (3)\صولو فريد الجود كلمات بان نور.wav",
    output_directory=r"D:\PhoenixVoiceEngine\workspace\phrase_segments",
)

output_path = (
    r"D:\PhoenixVoiceEngine\outputs\phrase_database.json"
)

os.makedirs(
    os.path.dirname(
        output_path
    ),
    exist_ok=True,
)

with open(
    output_path,
    "w",
    encoding="utf-8",
) as file:

    json.dump(
        database,
        file,
        ensure_ascii=False,
        indent=4,
    )

print(
    f"Segments: {len(database)}"
)

print()

print(
    database[:5]
)

print()

print(
    f"Output: {output_path}"
)

print()
print("STATUS: PASS")