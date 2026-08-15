import json
import os

from src.segmentation.musical_phrase_engine import (
    MusicalPhraseEngine,
)

print()
print("PhoenixVoiceEngine")
print("Musical Phrase Engine V1.0")
print("=" * 60)
print()

engine = MusicalPhraseEngine()

phrases = engine.build(
    audio_path=r"F:\مجلد جديد (3)\صولو فريد الجود كلمات بان نور.wav",
    words_json_path=r"D:\PhoenixVoiceEngine\outputs\lyrics\fareed_full_words.json",
    output_directory=r"D:\PhoenixVoiceEngine\workspace\musical_phrases",
)

output_path = (
    r"D:\PhoenixVoiceEngine\outputs\musical_phrase_database.json"
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
        phrases,
        file,
        ensure_ascii=False,
        indent=4,
    )

print(
    f"Phrases: {len(phrases)}"
)

print()

for phrase in phrases[:10]:

    print(
        phrase["text"]
    )

print()

print(
    f"Output: {output_path}"
)

print()
print("STATUS: PASS")