import wave
from pathlib import Path

print()
print("PhoenixVoiceEngine")
print("Saadah Segment Extractor V1.0")
print("=" * 60)

SOURCE = Path(
    r"D:\PhoenixVoiceEngine\samples\fareed_aljood.wav"
)

OUTPUT = Path(
    r"D:\PhoenixVoiceEngine\workspace\replacement_segments\saadah.wav"
)

START_TIME = 5.76
END_TIME = 6.70

with wave.open(str(SOURCE), "rb") as audio:

    sample_rate = audio.getframerate()
    channels = audio.getnchannels()
    sample_width = audio.getsampwidth()

    start_frame = int(
        START_TIME * sample_rate
    )

    end_frame = int(
        END_TIME * sample_rate
    )

    frame_count = (
        end_frame - start_frame
    )

    audio.setpos(start_frame)

    frames = audio.readframes(
        frame_count
    )

with wave.open(str(OUTPUT), "wb") as segment:

    segment.setnchannels(
        channels
    )

    segment.setsampwidth(
        sample_width
    )

    segment.setframerate(
        sample_rate
    )

    segment.writeframes(
        frames
    )

print()
print("Segment extracted successfully")
print(f"Saved: {OUTPUT}")
print(
    f"Duration: {END_TIME - START_TIME:.2f} seconds"
)

print()
print("STATUS: PASS")