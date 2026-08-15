import json
import os

from src.segmentation.breath_aware_phrase_engine import (
    BreathAwarePhraseEngine,
)

print()
print("PhoenixVoiceEngine")
print("Breath-Aware Phrase Engine V2")
print("=" * 60)
print()

engine = (
    BreathAwarePhraseEngine()
)

phrases = engine.build(
    audio_path=r"F:\مجلد جديد (3)\صولو فريد الجود كلمات بان نور.wav",
    words_json_path=r"D:\PhoenixVoiceEngine\outputs\lyrics\fareed_full_words.json",
    output_directory=r"D:\PhoenixVoiceEngine\workspace\breath_phrases",
)

output_path = (
    r"D:\PhoenixVoiceEngine\outputs\breath_phrase_database.json"
)

with open(
    output_path,
    "w",
    encoding="utf-8",
) as file:

    json.dump(
        phrases,
        file,
        ensure_ascii=False,
        indent=4,
    )

print(
    "Phrases:",
    len(phrases),
)

print()

for phrase in phrases[:15]:

    print(
        phrase["text"]
    )

print()

print(
    "STATUS: PASS"
)