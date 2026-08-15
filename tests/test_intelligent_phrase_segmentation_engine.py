import json
import os

from src.segmentation.intelligent_phrase_segmentation_engine import (
    IntelligentPhraseSegmentationEngine,
)

print()
print("PhoenixVoiceEngine")
print(
    "Intelligent Phrase Segmentation Engine V1.0"
)
print("=" * 60)
print()

engine = (
    IntelligentPhraseSegmentationEngine()
)

segments = engine.segment(
    audio_path=r"F:\مجلد جديد (3)\صولو فريد الجود كلمات بان نور.wav",
    words_json_path=r"D:\PhoenixVoiceEngine\outputs\lyrics\fareed_full_words.json",
    output_directory=r"D:\PhoenixVoiceEngine\workspace\intelligent_phrase_segments",
)

output_file = (
    r"D:\PhoenixVoiceEngine\outputs\intelligent_phrase_database.json"
)

os.makedirs(
    os.path.dirname(
        output_file
    ),
    exist_ok=True,
)

with open(
    output_file,
    "w",
    encoding="utf-8",
) as file:

    json.dump(
        segments,
        file,
        ensure_ascii=False,
        indent=4,
    )

print(
    f"Segments: {len(segments)}"
)

print()

for segment in segments[:5]:

    print(
        segment
    )

print()
print(
    f"Output: {output_file}"
)

print()
print("STATUS: PASS")