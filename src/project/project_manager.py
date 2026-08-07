from pathlib import Path
import json
from datetime import datetime


class ProjectManager:

    def create_project(self, project_name: str, artist_name: str):

        root = Path("Projects")

        project_folder = root / f"{artist_name} - {project_name}"

        project_folder.mkdir(parents=True, exist_ok=True)

        folders = [
            "audio",
            "analysis",
            "lyrics",
            "dna",
            "exports",
            "cache",
            "logs",
        ]

        for folder in folders:
            (project_folder / folder).mkdir(exist_ok=True)

        project_data = {
            "project_name": project_name,
            "artist_name": artist_name,
            "created_at": datetime.now().isoformat(),
            "version": "0.1"
        }

        with open(
            project_folder / "project.json",
            "w",
            encoding="utf-8"
        ) as f:

            json.dump(
                project_data,
                f,
                indent=4,
                ensure_ascii=False
            )

        return project_folder