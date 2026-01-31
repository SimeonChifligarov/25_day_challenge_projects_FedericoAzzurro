from __future__ import annotations

import os
from collections import Counter
from dataclasses import dataclass
from tkinter import Tk, filedialog
from typing import Iterable


# 1. Create a model for the data
@dataclass(frozen=True)
class Stats:
    folder: str
    num_files: int
    total_size_mb: float
    most_common_types: list[tuple[str, int]]


def select_folder(title: str = "Select folder to analyze") -> str:
    """Open a folder picker and return the selected folder path (or empty string)."""
    root: Tk = Tk()
    root.withdraw()
    return filedialog.askdirectory(title=title)


def iter_files(folder_path: str) -> Iterable[str]:
    """Yield full paths for all files inside folder_path (recursive)."""
    for current_dir, _, filenames in os.walk(folder_path):
        for filename in filenames:
            yield os.path.join(current_dir, filename)


def file_extension(path: str) -> str:
    """Return a lowercase extension (including dot), or empty string if none."""
    _, ext = os.path.splitext(path)
    return ext.lower()


def safe_getsize(path: str) -> int:
    """Return file size in bytes; return 0 if the file can't be accessed."""
    try:
        return os.path.getsize(path)
    except OSError:
        return 0


def bytes_to_mb(num_bytes: int) -> float:
    """Convert bytes to MB rounded to 2 decimals."""
    return round(num_bytes / (1024 * 1024), 2)


def collect_stats(folder_path: str) -> Stats:
    """Compute folder statistics."""
    file_count: int = 0
    total_size: int = 0
    extension_counter: Counter[str] = Counter()

    for path in iter_files(folder_path):
        file_count += 1
        total_size += safe_getsize(path)

        ext = file_extension(path)
        if ext:
            extension_counter[ext] += 1

    return Stats(
        folder=os.path.abspath(folder_path),
        num_files=file_count,
        total_size_mb=bytes_to_mb(total_size),
        most_common_types=extension_counter.most_common(5),
    )


# 2. Create a function that analyses the folder
def analyse_folder() -> Stats | None:
    folder_path: str = select_folder()
    if not folder_path:
        print("No folder selected.")
        return None
    return collect_stats(folder_path)


def main() -> None:
    stats: Stats | None = analyse_folder()

    if stats:
        print(f"Folder: {stats.folder}")
        print(f"Number of files: {stats.num_files}")
        print(f"Total size (MB): {stats.total_size_mb}")
        print("Most common file types:")
        for ext, count in stats.most_common_types:
            print(f"  {ext}: {count} files")


if __name__ == "__main__":
    main()
