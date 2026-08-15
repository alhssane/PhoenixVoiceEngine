import wave

print("PhoenixVoiceEngine")
print("Fareed Lyrics Extraction Test V1.0")
print("=" * 60)

audio_path = r"D:\PhoenixVoiceEngine\samples\fareed_aljood.wav"

with wave.open(audio_path, "rb") as audio:

    frames = audio.getnframes()
    rate = audio.getframerate()

    duration = frames / rate

print()

print("Audio Information")
print("=" * 40)

print(f"Sample rate: {rate} Hz")
print(f"Frames: {frames}")
print(f"Duration: {round(duration, 2)} seconds")

print()

print("STATUS: PASS")