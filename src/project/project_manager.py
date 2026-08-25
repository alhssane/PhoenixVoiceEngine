"""Project lifecycle management for Phoenix Voice Studio."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path


class ProjectManager:
    """Create and manage the on-disk project structure."""

    PROJECT_VERSION = "0.2.0"
    PROJECT_ROOT = Path("Projects")
    FOLDERS = (
        "audio",
        "analysis",
        "lyrics",
        "dna",
        "exports",
        "cache",
        "logs",
    )

    def __init__(self, root: Path | str | None = None) -> None:
        self.root = Path(root) if root is not None else self.PROJECT_ROOT

    def create_project(self, project_name: str, artist_name: str) -> Path:
        """Create a project and return its directory.

        Existing projects are preserved; their metadata is not overwritten.
        """
        project_name = self._validate_name(project_name, "Project name")
        artist_name = self._validate_name(artist_name, "Artist name")

        project_folder = self.root / f"{artist_name} - {project_name}"
        project_folder.mkdir(parents=True, exist_ok=True)

        for folder in self.FOLDERS:
            (project_folder / folder).mkdir(exist_ok=True)

        project_file = project_folder / "project.json"
        if not project_file.exists():
            project_data = {
                "project_name": project_name,
                "artist_name": artist_name,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "version": self.PROJECT_VERSION,
            }
            project_file.write_text(
                json.dumps(project_data, indent=4, ensure_ascii=False),
                encoding="utf-8",
            )

        return project_folder

    @staticmethod
    def _validate_name(value: str, label: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError(f"{label} cannot be empty")
        if any(char in value for char in '/\\:*?\"<>|'):
            raise ValueError(f"{label} contains an invalid path character")
        return value
