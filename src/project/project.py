"""
Phoenix Voice Studio
Project Object
Version: 1.0
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from uuid import uuid4


@dataclass
class Project:

    name: str
    artist: str

    project_id: str = field(default_factory=lambda: str(uuid4()))

    created_at: str = field(
        default_factory=lambda: datetime.now().isoformat()
    )

    updated_at: str = field(
        default_factory=lambda: datetime.now().isoformat()
    )

    version: str = "1.0"

    audio_file: str = ""

    project_path: str = ""

    status: str = "NEW"

    def rename(self, new_name: str):

        self.name = new_name
        self.touch()

    def set_audio(self, audio_path: str):

        self.audio_file = audio_path
        self.touch()

    def set_project_path(self, path: str):

        self.project_path = str(Path(path))
        self.touch()

    def touch(self):

        self.updated_at = datetime.now().isoformat()

    def to_dict(self):

        return {
            "project_id": self.project_id,
            "name": self.name,
            "artist": self.artist,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "version": self.version,
            "audio_file": self.audio_file,
            "project_path": self.project_path,
            "status": self.status,
        }

    @classmethod
    def from_dict(cls, data):

        project = cls(
            name=data["name"],
            artist=data["artist"],
        )

        project.project_id = data["project_id"]
        project.created_at = data["created_at"]
        project.updated_at = data["updated_at"]
        project.version = data["version"]
        project.audio_file = data["audio_file"]
        project.project_path = data["project_path"]
        project.status = data["status"]

        return project