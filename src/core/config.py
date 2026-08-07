"""
Phoenix Voice Studio
Configuration System

This module contains all application paths and
global configuration values.
"""

from pathlib import Path


# --------------------------------------------------
# Project Information
# --------------------------------------------------

PROJECT_NAME = "Phoenix Voice Studio"

PROJECT_VERSION = "0.1.0-alpha"


# --------------------------------------------------
# Root Directory
# --------------------------------------------------

ROOT_DIR = Path(__file__).resolve().parents[2]


# --------------------------------------------------
# Main Directories
# --------------------------------------------------

DATASETS_DIR = ROOT_DIR / "datasets"

MODELS_DIR = ROOT_DIR / "models"

DOCS_DIR = ROOT_DIR / "docs"

TOOLS_DIR = ROOT_DIR / "tools"

TESTS_DIR = ROOT_DIR / "tests"

TEMP_DIR = ROOT_DIR / "temp"

LOGS_DIR = ROOT_DIR / "logs"

PROJECTS_DIR = ROOT_DIR / "projects"


# --------------------------------------------------
# Create Missing Directories
# --------------------------------------------------

REQUIRED_DIRECTORIES = [

    DATASETS_DIR,

    MODELS_DIR,

    DOCS_DIR,

    TOOLS_DIR,

    TESTS_DIR,

    TEMP_DIR,

    LOGS_DIR,

    PROJECTS_DIR,

]

for directory in REQUIRED_DIRECTORIES:

    directory.mkdir(parents=True, exist_ok=True)