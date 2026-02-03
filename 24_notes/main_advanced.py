from __future__ import annotations

from pathlib import Path
from datetime import datetime

NOTES_FILE = Path("notes.txt")


def display_menu() -> None:
    print("\nNote-Taking Application")
    print("1. Add a Note")
    print("2. View Notes")
    print("3. Delete a Note")
    print("4. Exit")


def load_notes() -> list[str]:
    if not NOTES_FILE.exists():
        return []
    try:
        return NOTES_FILE.read_text(encoding="utf-8").splitlines()
    except OSError as e:
        print(f"Error reading notes file: {e}")
        return []


def save_notes(notes: list[str]) -> None:
    try:
        NOTES_FILE.write_text("\n".join(notes) + ("\n" if notes else ""), encoding="utf-8")
    except OSError as e:
        print(f"Error writing notes file: {e}")


def add_note() -> None:
    note = input("Enter your note: ").strip()
    if not note:
        print("Note cannot be empty.")
        return

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    line = f"[{timestamp}] {note}"

    try:
        with NOTES_FILE.open("a", encoding="utf-8") as f:
            f.write(line + "\n")
        print("Note added successfully.")
    except OSError as e:
        print(f"Error saving note: {e}")


def view_notes(notes: list[str] | None = None) -> list[str]:
    notes = load_notes() if notes is None else notes

    if not notes:
        print("No notes found.")
        return []

    print(f"\nYour Notes ({len(notes)}):")
    for i, note in enumerate(notes, start=1):
        print(f"{i}. {note}")
    return notes


def prompt_int(prompt: str) -> int | None:
    raw = input(prompt).strip()
    if raw == "":
        return None
    try:
        return int(raw)
    except ValueError:
        return -1


def delete_note() -> None:
    notes = load_notes()
    if not notes:
        print("No notes found.")
        return

    view_notes(notes)

    while True:
        note_num = prompt_int("Enter the note number to delete (Enter to cancel): ")
        if note_num is None:
            print("Delete cancelled.")
            return
        if note_num == -1:
            print("Please enter a valid number.")
            continue
        if not (1 <= note_num <= len(notes)):
            print("Invalid note number.")
            continue

        to_delete = notes[note_num - 1]
        confirm = input(f'Delete "{to_delete}"? (y/N): ').strip().lower()
        if confirm == "y":
            del notes[note_num - 1]
            save_notes(notes)
            print("Note deleted successfully.")
        else:
            print("Delete cancelled.")
        return


def main() -> None:
    while True:
        display_menu()
        choice = input("Choose an option: ").strip()

        if choice == "1":
            add_note()
        elif choice == "2":
            view_notes()
        elif choice == "3":
            delete_note()
        elif choice == "4":
            print("Exiting the application.")
            break
        else:
            print("Invalid choice. Please try again.")


if __name__ == "__main__":
    main()
