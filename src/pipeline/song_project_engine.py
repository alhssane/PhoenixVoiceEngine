from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from src.project.project_manager import ProjectManager
from src.transcription.full_song_transcription_engine import FullSongTranscriptionEngine
from src.trainer.artist_training_engine import ArtistTrainingEngine
from src.synthesis.hybrid_singing_backend import HybridSingingBackend
from src.synthesis.synthesis_backend import SynthesisRequest, SynthesisResult


class SongProjectEngine:
    """End-to-end project coordinator for clean-vocal lyric editing."""

    VERSION = "1.1.0"

    def __init__(self, projects_root: str | Path = "Projects") -> None:
        self.projects_root = Path(projects_root)
        self.transcriber = FullSongTranscriptionEngine()
        self.trainer = ArtistTrainingEngine()

    def prepare(
        self,
        audio_path: str | Path,
        project_name: str,
        artist_name: str,
    ) -> dict[str, Any]:
        audio_path = Path(audio_path)
        if not audio_path.is_file():
            raise FileNotFoundError(f"Audio file not found: {audio_path}")

        project = ProjectManager(self.projects_root).create_project(
            project_name,
            artist_name,
        )
        imported_audio = project / "audio" / audio_path.name
        imported_audio.write_bytes(audio_path.read_bytes())

        lyrics_path = project / "lyrics" / "original_words.json"
        transcription = self.transcriber.transcribe(
            imported_audio,
            output_path=lyrics_path,
            language="ar",
        )

        profile_path = project / "dna" / "artist_profile.json"
        training = self.trainer.train(
            imported_audio,
            lyrics_path,
            profile_path,
            artist_name=artist_name,
        )

        manifest = {
            "schema_version": "1.1",
            "project": str(project),
            "audio": str(imported_audio),
            "lyrics": str(lyrics_path),
            "profile": str(profile_path),
            "transcription": transcription,
            "training": {
                "status": training["training_status"],
                "word_count": training["word_count"],
            },
            "language": "ar",
        }
        manifest_path = project / "project_manifest.json"
        manifest_path.write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        return manifest

    def synthesize_edit(
        self,
        project_path: str | Path,
        target_lyrics: str,
        output_name: str = "generated.wav",
    ) -> SynthesisResult:
        project = Path(project_path)
        manifest_path = project / "project_manifest.json"
        if not manifest_path.is_file():
            raise FileNotFoundError(f"Project manifest not found: {manifest_path}")

        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        audio_path = Path(manifest["audio"])
        lyrics_path = Path(manifest["lyrics"])
        words = json.loads(lyrics_path.read_text(encoding="utf-8"))
        reference_lyrics = " ".join(item["word"] for item in words)
        target_lyrics = target_lyrics.strip()
        if not target_lyrics:
            raise ValueError("Target lyrics cannot be empty.")

        output_path = project / "exports" / output_name
        request = SynthesisRequest(
            reference_audio=audio_path,
            melody_audio=audio_path,
            reference_lyrics=reference_lyrics,
            target_lyrics=target_lyrics,
            output_audio=output_path,
            language="ar",
            preserve_style=True,
            preserve_melody=True,
        )

        # Production path: singing synthesis first, then conversion to the
        # reference singer's timbre. Model-specific CLIs stay outside Phoenix.
        backend = HybridSingingBackend()
        if not backend.supports("ar"):
            raise RuntimeError(
                "Arabic hybrid singing backend is not configured. Set both "
                "PHOENIX_SVS_COMMAND and PHOENIX_VC_COMMAND to real, "
                "authorized Arabic-capable model runners before generating audio."
            )

        result = backend.synthesize(request)
        if result.output_audio.stat().st_size == 0:
            raise RuntimeError("Synthesis produced an empty output file.")
        return result
