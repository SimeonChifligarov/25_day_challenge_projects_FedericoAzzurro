from __future__ import annotations

import mimetypes
import os
from dataclasses import dataclass
from pathlib import Path
from tkinter import Tk, filedialog
from typing import Counter, Iterable, Literal
from collections import Counter as CounterCls

TypeMode = Literal["extension", "mime"]


# 1. Create a model for the data
@dataclass(frozen=True)
class Stats:
    folder: str
    num_files: int
    total_size_mb: float
    most_common_types: list[tuple[str, int]]
    skipped_files: int
    skipped_dirs: int


def select_folder(title: str = "Select folder to analyze") -> str:
    """Open a folder picker and return the selected folder path (or empty string)."""
    root: Tk = Tk()
    root.withdraw()
    try:
        return filedialog.askdirectory(title=title)
    finally:
        # Ensure the hidden root window is cleaned up
        root.destroy()


def iter_files(folder: Path) -> Iterable[Path]:
    """
    Yield all files under `folder` (recursive), skipping directories that
    can't be accessed.

    Uses os.scandir for good performance on large trees.
    """
    try:
        with os.scandir(folder) as it:
            for entry in it:
                # Avoid following symlinks by default to prevent cycles.
                try:
                    if entry.is_file(follow_symlinks=False):
                        yield Path(entry.path)
                    elif entry.is_dir(follow_symlinks=False):
                        yield from iter_files(Path(entry.path))
                except OSError:
                    # Can't stat this entry -> ignore it
                    continue
    except OSError:
        # Can't scan this directory -> caller may count it as skipped
        return


def safe_getsize(path: Path) -> int | None:
    """Return file size in bytes; return None if the file can't be accessed."""
    try:
        return path.stat().st_size
    except OSError:
        return None


def bytes_to_mb(num_bytes: int) -> float:
    """Convert bytes to MB rounded to 2 decimals."""
    return round(num_bytes / (1024 * 1024), 2)


def file_type_key(path: Path, mode: TypeMode) -> str:
    """
    Return a "type" key for counting:
    - extension mode: ".txt", ".jpg", ...
    - mime mode: "text/plain", "image/jpeg", ...
    """
    if mode == "extension":
        return path.suffix.lower()

    guessed, _ = mimetypes.guess_type(str(path))
    return guessed or ""


def collect_stats(
        folder_path: str | Path,
        *,
        top_n: int = 5,
        include_no_type: bool = False,
        type_mode: TypeMode = "extension",
) -> Stats:
    """
    Compute folder statistics.

    - Skips inaccessible files (they are not counted in num_files or total size)
    - Optionally counts missing/unknown type under "<no_type>"
    - Supports type_mode="extension" or "mime"
    """
    folder = Path(folder_path).expanduser().resolve()

    file_count: int = 0
    total_size: int = 0
    skipped_files: int = 0
    skipped_dirs: int = 0
    type_counter: Counter[str] = CounterCls()

    # Count skipped dirs by attempting scandir on each directory during traversal.
    # We do this by wrapping iter_files with an explicit stack so we can notice failures.
    stack: list[Path] = [folder]
    while stack:
        current = stack.pop()
        try:
            with os.scandir(current) as it:
                for entry in it:
                    try:
                        if entry.is_file(follow_symlinks=False):
                            path = Path(entry.path)
                            size = safe_getsize(path)
                            if size is None:
                                skipped_files += 1
                                continue

                            file_count += 1
                            total_size += size

                            key = file_type_key(path, type_mode)
                            if key:
                                type_counter[key] += 1
                            elif include_no_type:
                                type_counter["<no_type>"] += 1

                        elif entry.is_dir(follow_symlinks=False):
                            stack.append(Path(entry.path))
                    except OSError:
                        # Entry exists but can't be inspected
                        skipped_files += 1
                        continue
        except OSError:
            skipped_dirs += 1
            continue

    return Stats(
        folder=str(folder),
        num_files=file_count,
        total_size_mb=bytes_to_mb(total_size),
        most_common_types=type_counter.most_common(top_n),
        skipped_files=skipped_files,
        skipped_dirs=skipped_dirs,
    )


def format_report(stats: Stats) -> str:
    """Create a printable report string (no side effects)."""
    lines: list[str] = [
        f"Folder: {stats.folder}",
        f"Number of files: {stats.num_files}",
        f"Total size (MB): {stats.total_size_mb}",
        "Most common file types:",
    ]

    if stats.most_common_types:
        lines.extend([f"  {k}: {v} files" for k, v in stats.most_common_types])
    else:
        lines.append("  (none)")

    if stats.skipped_files or stats.skipped_dirs:
        lines.append("Skipped due to access errors:")
        lines.append(f"  Files: {stats.skipped_files}")
        lines.append(f"  Dirs:  {stats.skipped_dirs}")

    return "\n".join(lines)


def analyse_folder() -> Stats | None:
    """UI wrapper: asks the user for a folder, then returns computed Stats."""
    folder_path = select_folder()
    if not folder_path:
        print("No folder selected.")
        return None

    # Defaults keep behavior close to the original, while supporting improvements.
    return collect_stats(
        folder_path,
        top_n=5,
        include_no_type=False,  # set True if you want "<no_type>" counted
        type_mode="extension",  # set "mime" to count MIME types instead
    )


def main() -> None:
    stats = analyse_folder()
    if stats is not None:
        print(format_report(stats))


if __name__ == "__main__":
    main()
