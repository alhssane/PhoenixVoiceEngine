from pathlib import Path
import json

from faster_whisper import WhisperModel

print()
print("PhoenixVoiceEngine")
print("Fareed Real Transcription V1.0")
print("=" * 60)

audio_path = Path(
    r"D:\PhoenixVoiceEngine\samples\fareed_aljood.wav"
)

output_dir = Path(
    r"D:\PhoenixVoiceEngine\outputs\lyrics"
)

output_dir.mkdir(
    parents=True,
    exist_ok=True
)

model = WhisperModel(
    "small",
    device="cpu",
    compute_type="int8"
)

segments, info = model.transcribe(
    str(audio_path),
    language="ar",
    word_timestamps=True
)

results = []

for segment in segments:

    if not segment.words:
        continue

    for word in segment.words:

        results.append(
            {
                "word": word.word.strip(),
                "start": round(word.start, 2),
                "end": round(word.end, 2),
                "duration": round(
                    word.end - word.start,
                    2
                )
            }
        )

json_path = (
    output_dir
    / "fareed_words.json"
)

with open(
    json_path,
    "w",
    encoding="utf-8"
) as f:

    json.dump(
        results,
        f,
        ensure_ascii=False,
        indent=4
    )

print()
print("Words extracted:", len(results))
print("Saved:", json_path)

print()
print("First 20 words")
print("=" * 40)

for item in results[:20]:

    print(
        f"{item['start']}s -> "
        f"{item['end']}s | "
        f"{item['word']}"
    )

print()
print("STATUS: PASS")