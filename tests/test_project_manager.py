from pathlib import Path

import pytest

from src.project.project_manager import ProjectManager


def test_create_project_creates_expected_structure(tmp_path: Path):
    manager = ProjectManager(tmp_path / "Projects")

    project = manager.create_project("ارحبي", "راشد الماجد")

    assert project.name == "راشد الماجد - ارحبي"
    assert (project / "project.json").exists()
    for folder in manager.FOLDERS:
        assert (project / folder).is_dir()


def test_create_project_does_not_overwrite_existing_metadata(tmp_path: Path):
    manager = ProjectManager(tmp_path / "Projects")
    project = manager.create_project("Song", "Artist")
    metadata = project / "project.json"
    original = metadata.read_text(encoding="utf-8")

    manager.create_project("Song", "Artist")

    assert metadata.read_text(encoding="utf-8") == original


def test_create_project_rejects_empty_name(tmp_path: Path):
    manager = ProjectManager(tmp_path / "Projects")

    with pytest.raises(ValueError, match="cannot be empty"):
        manager.create_project("", "Artist")


def test_create_project_rejects_path_separator(tmp_path: Path):
    manager = ProjectManager(tmp_path / "Projects")

    with pytest.raises(ValueError, match="invalid path character"):
        manager.create_project("Song/Bad", "Artist")
