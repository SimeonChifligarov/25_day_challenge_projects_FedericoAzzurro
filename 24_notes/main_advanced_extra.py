from __future__ import annotations

from pathlib import Path

NOTES_PATH = Path("notes.txt")
FILE_ENCODING = "utf-8"


def display_menu() -> None:
    """Print the main menu options."""
    print("Note-Taking Application")
    print("1. Add a Note")
    print("2. View Notes")
    print("3. Delete a Note")
    print("4. Exit")


def read_notes() -> list[str]:
    """
    Read notes from disk.

    Returns:
        A list of note lines (including trailing newlines), or an empty list if
        the file doesn't exist.
    """
    try:
        with NOTES_PATH.open("r", encoding=FILE_ENCODING) as f:
            return f.readlines()
    except FileNotFoundError:
        return []


def write_notes(notes: list[str]) -> None:
    """Overwrite the notes file with the provided note lines."""
    with NOTES_PATH.open("w", encoding=FILE_ENCODING) as f:
        f.writelines(notes)


def add_note() -> None:
    """Prompt the user and append a note to the notes file."""
    note = input("Enter your note: ")
    with NOTES_PATH.open("a", encoding=FILE_ENCODING) as f:
        f.write(f"{note}\n")
    print("Note added successfully.")


def view_notes(notes: list[str] | None = None) -> None:
    """Display all notes. If notes is None, reads from disk."""
    if notes is None:
        notes = read_notes()

    if notes:
        print("\nYour Notes:")
        for i, note in enumerate(notes, start=1):
            print(f"{i}. {note.strip()}")
    else:
        print("No notes found.")


def delete_note() -> None:
    """Show notes and delete a selected note by number."""
    notes = read_notes()
    view_notes(notes)

    if not notes:
        return

    try:
        note_num = int(input("Enter the note number to delete: "))
    except ValueError:
        print("Please enter a valid number.")
        return

    if 1 <= note_num <= len(notes):
        del notes[note_num - 1]
        write_notes(notes)
        print("Note deleted successfully.")
    else:
        print("Invalid note number.")


def main() -> None:
    """Run the note-taking application loop."""
    while True:
        display_menu()
        choice = input("Choose an option: ")

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
