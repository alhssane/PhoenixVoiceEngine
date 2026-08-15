import json
import os

from src.segmentation.breath_detection_engine import (
    BreathDetectionEngine,
)

print()
print("PhoenixVoiceEngine")
print("Breath Detection Engine V1.0")
print("=" * 60)
print()

engine = BreathDetectionEngine()

pauses = engine.detect(
    audio_path=r"F:\مجلد جديد (3)\صولو فريد الجود كلمات بان نور.wav",
)

output_path = (
    r"D:\PhoenixVoiceEngine\outputs\breath_points.json"
)

with open(
    output_path,
    "w",
    encoding="utf-8",
) as file:

    json.dump(
        pauses,
        file,
        ensure_ascii=False,
        indent=4,
    )

print(
    f"Breath points: {len(pauses)}"
)

print()

for pause in pauses[:20]:

    print(
        pause
    )

print()

print(
    f"Output: {output_path}"
)

print()

print(
    "STATUS: PASS"
)