"""
Phoenix Voice Studio
Main Application
"""

import os

from src.project.project_manager import ProjectManager
from src.pipeline.audio_import_pipeline import AudioImportPipeline

APP_NAME = "Phoenix Voice Studio"
VERSION = "0.1.0"


def clear():
    os.system("cls" if os.name == "nt" else "clear")


def header():
    print("=" * 50)
    print(APP_NAME)
    print(f"Version : {VERSION}")
    print("=" * 50)
    print()


def menu():
    print("1. New Project")
    print("2. Open Project")
    print("3. Audio Inspector")
    print("4. Settings")
    print("5. Exit")
    print()


def pause():
    input("\nPress Enter to continue...")


def new_project():

    print("\n=== Create New Project ===\n")

    project_name = input("Project Name : ").strip()
    artist_name = input("Artist Name  : ").strip()

    if not project_name:
        print("\nProject name cannot be empty.")
        pause()
        return

    if not artist_name:
        print("\nArtist name cannot be empty.")
        pause()
        return

    manager = ProjectManager()

    project_path = manager.create_project(
        project_name,
        artist_name,
    )

    print("\n===================================")
    print("Project Created Successfully")
    print(f"Location : {project_path}")
    print("===================================")

    pause()


def audio_inspector():

    print("\n=== Audio Inspector ===\n")

    audio_file = input("Audio File Path : ").strip()

    if not audio_file:
        print("\nNo file selected.")
        pause()
        return

    try:

        pipeline = AudioImportPipeline()

        pipeline.run(audio_file)

    except Exception as e:

        print("\n===================================")
        print("ERROR")
        print("-----------------------------------")
        print(e)
        print("===================================")

    pause()


def main():

    while True:

        clear()

        header()

        menu()

        choice = input("Select option : ").strip()

        if choice == "1":

            new_project()

        elif choice == "2":

            print("\nOpen Project (Coming Soon)")
            pause()

        elif choice == "3":

            audio_inspector()

        elif choice == "4":

            print("\nSettings (Coming Soon)")
            pause()

        elif choice == "5":

            print("\nGood Bye.")
            break

        else:

            print("\nInvalid option.")
            pause()


if __name__ == "__main__":
    main()