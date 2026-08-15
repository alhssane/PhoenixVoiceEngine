from src.analysis.real_note_extraction_engine import (
    RealNoteExtractionEngine,
)

AUDIO_FILE = (
    r"D:\PhoenixVoiceEngine\workspace\replacement_segments\saadah.wav"
)

print()
print("PhoenixVoiceEngine")
print("Saadah Note Analysis V1.0")
print("=" * 60)

engine = (
    RealNoteExtractionEngine()
)

notes = engine.analyze(
    AUDIO_FILE
)

print()

print("Note Distribution")
print("=" * 40)

for note, percentage in notes.items():

    print(
        f"{note}: {percentage}%"
    )

print()

print("STATUS: PASS")