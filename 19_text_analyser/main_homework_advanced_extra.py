from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from pathlib import Path
import re
from typing import Iterable

DEFAULT_PUNCTUATION: str = ".!?:;"
WORD_PATTERN: re.Pattern[str] = re.compile(r"\b\w+\b")


@dataclass(frozen=True)
class TextStats:
    word_count: int
    comma_count: int
    char_count_incl_ws: int
    whitespace_count: int
    punctuation_counts: dict[str, int]
    average_word_length: float
    top_words: list[tuple[str, int]]


def _count_chunk(
        chunk: str,
        *,
        punctuation_set: set[str],
        word_counter: Counter[str],
) -> tuple[int, int, int, int, Counter[str]]:
    """
    Returns:
      word_count_delta,
      total_word_length_delta,
      comma_count_delta,
      whitespace_count_delta,
      punctuation_counts_delta (Counter)
    """
    words = WORD_PATTERN.findall(chunk.lower())
    word_counter.update(words)

    word_count_delta = len(words)
    total_word_length_delta = sum(len(w) for w in words)

    comma_count_delta = chunk.count(",")
    whitespace_count_delta = sum(ch.isspace() for ch in chunk)

    punctuation_counts_delta: Counter[str] = Counter()
    for ch in chunk:
        if ch in punctuation_set:
            punctuation_counts_delta[ch] += 1

    return (
        word_count_delta,
        total_word_length_delta,
        comma_count_delta,
        whitespace_count_delta,
        punctuation_counts_delta,
    )


def analyze_file_full_read(
        path: Path,
        *,
        punctuation: Iterable[str],
        top_n: int,
        encoding: str = "utf-8",
) -> TextStats:
    text = path.read_text(encoding=encoding, errors="replace")
    return analyze_text(text, punctuation=punctuation, top_n=top_n)


def analyze_file_streaming(
        path: Path,
        *,
        punctuation: Iterable[str],
        top_n: int,
        encoding: str = "utf-8",
) -> TextStats:
    punctuation_list = list(punctuation)
    punctuation_set = set(punctuation_list)

    word_counter: Counter[str] = Counter()
    punctuation_counter: Counter[str] = Counter()

    word_count = 0
    total_word_length = 0
    comma_count = 0
    char_count_incl_ws = 0
    whitespace_count = 0

    with path.open("r", encoding=encoding, errors="replace") as file:
        for line in file:
            char_count_incl_ws += len(line)

            (
                wc_delta,
                wlen_delta,
                comma_delta,
                ws_delta,
                punct_delta,
            ) = _count_chunk(line, punctuation_set=punctuation_set, word_counter=word_counter)

            word_count += wc_delta
            total_word_length += wlen_delta
            comma_count += comma_delta
            whitespace_count += ws_delta
            punctuation_counter.update(punct_delta)

    avg_word_length = (total_word_length / word_count) if word_count else 0.0
    punctuation_counts_ordered = {p: punctuation_counter.get(p, 0) for p in punctuation_list}

    return TextStats(
        word_count=word_count,
        comma_count=comma_count,
        char_count_incl_ws=char_count_incl_ws,
        whitespace_count=whitespace_count,
        punctuation_counts=punctuation_counts_ordered,
        average_word_length=avg_word_length,
        top_words=word_counter.most_common(max(top_n, 0)),
    )


def analyze_text(text: str, *, punctuation: Iterable[str], top_n: int) -> TextStats:
    punctuation_list = list(punctuation)
    punctuation_set = set(punctuation_list)

    word_counter: Counter[str] = Counter()
    punctuation_counter: Counter[str] = Counter()

    (
        word_count,
        total_word_length,
        comma_count,
        whitespace_count,
        punct_delta,
    ) = _count_chunk(text, punctuation_set=punctuation_set, word_counter=word_counter)

    punctuation_counter.update(punct_delta)

    avg_word_length = (total_word_length / word_count) if word_count else 0.0
    punctuation_counts_ordered = {p: punctuation_counter.get(p, 0) for p in punctuation_list}

    return TextStats(
        word_count=word_count,
        comma_count=comma_count,
        char_count_incl_ws=len(text),
        whitespace_count=whitespace_count,
        punctuation_counts=punctuation_counts_ordered,
        average_word_length=avg_word_length,
        top_words=word_counter.most_common(max(top_n, 0)),
    )


def print_report(stats: TextStats) -> None:
    line = "-" * 30
    print(line)
    print(f"Word count: {stats.word_count}")
    print(f"Commas used: {stats.comma_count}")
    print(f"Character count (incl. whitespaces): {stats.char_count_incl_ws}")
    print(f"Whitespace characters: {stats.whitespace_count}")
    print("")
    print("Punctuation marks:")
    for mark, count in stats.punctuation_counts.items():
        print(f" > {mark}: {count}")
    print("")
    print(f"Average word length: {stats.average_word_length:.2f}")
    print("")
    print(f"Top {len(stats.top_words)} most used words:")
    for word, count in stats.top_words:
        print(f" > {word}: {count}")
    print(line)


def _ask_int(prompt: str, default: int) -> int:
    raw = input(f"{prompt} [{default}]: ").strip()
    if not raw:
        return default
    try:
        value = int(raw)
    except ValueError:
        return default
    return max(value, 0)


def _ask_yes_no(prompt: str, default_yes: bool) -> bool:
    default = "y" if default_yes else "n"
    raw = input(f"{prompt} (y/n) [{default}]: ").strip().lower()
    if not raw:
        return default_yes
    return raw.startswith("y")


def main() -> None:
    filename = input("File to analyse [sample.txt]: ").strip() or "sample.txt"
    path = Path(filename)

    top_n = _ask_int("How many top words to show", default=3)
    punctuation_str = input(f"Punctuation to count [{DEFAULT_PUNCTUATION}]: ").strip() or DEFAULT_PUNCTUATION
    use_streaming = _ask_yes_no("Use streaming mode for large files?", default_yes=False)

    try:
        if use_streaming:
            stats = analyze_file_streaming(path, punctuation=punctuation_str, top_n=top_n)
        else:
            stats = analyze_file_full_read(path, punctuation=punctuation_str, top_n=top_n)
    except FileNotFoundError:
        print(f"File not found: {path}")
        return
    except OSError as exc:
        print(f"Could not read '{path}': {exc}")
        return

    print_report(stats)


if __name__ == "__main__":
    main()
