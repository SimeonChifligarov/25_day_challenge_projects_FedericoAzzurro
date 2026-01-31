from __future__ import annotations

import argparse
import json
import logging
import mimetypes
import os
from collections import Counter
from contextlib import contextmanager
from dataclasses import asdict, dataclass
from pathlib import Path
from tkinter import Tk, filedialog
from typing import Iterable, Iterator, Literal

TypeMode = Literal["extension", "mime"]
log = logging.getLogger(__name__)


# -----------------------------
# Model
# -----------------------------
@dataclass(frozen=True, slots=True)
class Stats:
    folder: str
    num_files: int
    total_size_mb: float
    most_common_types: list[tuple[str, int]]
    skipped_files: int
    skipped_dirs: int


# -----------------------------
# Small utilities (pure / reusable)
# -----------------------------
def bytes_to_mb(num_bytes: int) -> float:
    return round(num_bytes / (1024 * 1024), 2)


def type_key(path: Path, mode: TypeMode) -> str:
    if mode == "extension":
        return path.suffix.lower()
    guessed, _ = mimetypes.guess_type(path.as_posix())
    return guessed or ""


def safe_size(path: Path) -> int | None:
    try:
        return path.stat().st_size
    except OSError as e:
        log.debug("Skipping file (stat failed): %s (%s)", path, e)
        return None


# -----------------------------
# GUI (isolated side effects)
# -----------------------------
@contextmanager
def hidden_tk_root() -> Iterator[Tk]:
    root = Tk()
    root.withdraw()
    try:
        yield root
    finally:
        root.destroy()


def pick_folder(title: str = "Select folder to analyze") -> Path | None:
    with hidden_tk_root():
        selected = filedialog.askdirectory(title=title)
    return Path(selected).expanduser().resolve() if selected else None


# -----------------------------
# Core analysis (fast, testable)
# -----------------------------
@dataclass(frozen=True, slots=True)
class AnalysisConfig:
    top_n: int = 5
    type_mode: TypeMode = "extension"
    include_no_type: bool = False
    follow_symlinks: bool = False


def iter_entries(folder: Path, *, follow_symlinks: bool) -> Iterable[os.DirEntry[str]]:
    """
    Iterate directory entries (non-recursive) using os.scandir for speed.
    Separate function makes it easy to mock in tests.
    """
    with os.scandir(folder) as it:
        yield from it


def analyze_folder(folder: Path, config: AnalysisConfig) -> Stats:
    folder = folder.expanduser().resolve()

    total_bytes = 0
    file_count = 0
    skipped_files = 0
    skipped_dirs = 0
    counter: Counter[str] = Counter()

    # Iterative DFS avoids recursion depth issues on huge trees.
    stack: list[Path] = [folder]

    while stack:
        current = stack.pop()
        try:
            for entry in iter_entries(current, follow_symlinks=config.follow_symlinks):
                try:
                    if entry.is_dir(follow_symlinks=config.follow_symlinks):
                        stack.append(Path(entry.path))
                        continue

                    if not entry.is_file(follow_symlinks=config.follow_symlinks):
                        # skip special files (sockets, devices, etc.)
                        continue

                    path = Path(entry.path)
                    size = safe_size(path)
                    if size is None:
                        skipped_files += 1
                        continue

                    file_count += 1
                    total_bytes += size

                    key = type_key(path, config.type_mode)
                    if key:
                        counter[key] += 1
                    elif config.include_no_type:
                        counter["<no_type>"] += 1

                except OSError as e:
                    # Can't inspect this entry (permissions, race conditions, etc.)
                    skipped_files += 1
                    log.debug("Skipping entry: %s (%s)", entry.path, e)

        except OSError as e:
            skipped_dirs += 1
            log.debug("Skipping dir (scan failed): %s (%s)", current, e)

    return Stats(
        folder=str(folder),
        num_files=file_count,
        total_size_mb=bytes_to_mb(total_bytes),
        most_common_types=counter.most_common(config.top_n),
        skipped_files=skipped_files,
        skipped_dirs=skipped_dirs,
    )


# -----------------------------
# Presentation (pure)
# -----------------------------
def format_report(stats: Stats) -> str:
    lines: list[str] = [
        f"Folder: {stats.folder}",
        f"Number of files: {stats.num_files}",
        f"Total size (MB): {stats.total_size_mb}",
        "Most common file types:",
    ]

    if stats.most_common_types:
        lines.extend(f"  {k}: {v} files" for k, v in stats.most_common_types)
    else:
        lines.append("  (none)")

    if stats.skipped_files or stats.skipped_dirs:
        lines.append("Skipped due to access errors:")
        lines.append(f"  Files: {stats.skipped_files}")
        lines.append(f"  Dirs:  {stats.skipped_dirs}")

    return "\n".join(lines)


# -----------------------------
# CLI (advanced, still single-file)
# -----------------------------
def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Analyze a folder: file count, size, and most common types.")
    p.add_argument("folder", nargs="?", help="Folder to analyze. If omitted, a GUI picker is used (unless --no-gui).")
    p.add_argument("--top", type=int, default=5, help="How many common types to show (default: 5).")
    p.add_argument("--mode", choices=("extension", "mime"), default="extension", help="Type counting mode.")
    p.add_argument("--include-no-type", action="store_true", help="Count missing/unknown types as <no_type>.")
    p.add_argument("--follow-symlinks", action="store_true", help="Follow symlinks (can risk cycles on some FS).")
    p.add_argument("--json", dest="as_json", action="store_true", help="Output JSON instead of text.")
    p.add_argument("--no-gui", action="store_true", help="Do not use GUI picker; require a folder arg.")
    p.add_argument("--log-level", default="WARNING", help="Logging level (DEBUG, INFO, WARNING, ERROR).")
    return p.parse_args()


def configure_logging(level: str) -> None:
    numeric = getattr(logging, level.upper(), None)
    if not isinstance(numeric, int):
        numeric = logging.WARNING
    logging.basicConfig(level=numeric, format="%(levelname)s: %(message)s")


def main() -> int:
    args = parse_args()
    configure_logging(args.log_level)

    config = AnalysisConfig(
        top_n=max(1, args.top),
        type_mode=args.mode,
        include_no_type=args.include_no_type,
        follow_symlinks=args.follow_symlinks,
    )

    folder: Path | None
    if args.folder:
        folder = Path(args.folder)
    elif args.no_gui:
        print("Error: folder argument required when --no-gui is used.")
        return 2
    else:
        folder = pick_folder()
        if folder is None:
            print("No folder selected.")
            return 1

    if not folder.exists() or not folder.is_dir():
        print(f"Error: not a directory: {folder}")
        return 2

    stats = analyze_folder(folder, config)

    if args.as_json:
        print(json.dumps(asdict(stats), ensure_ascii=False, indent=2))
    else:
        print(format_report(stats))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
