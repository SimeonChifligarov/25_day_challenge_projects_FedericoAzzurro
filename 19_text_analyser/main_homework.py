from collections import Counter
import re

PUNCTUATION_MARKS: tuple[str, ...] = (".", "!", "?", ":", ";")


def analyse(filename: str) -> None:
    with open(filename, "r", encoding="utf-8") as file:
        text: str = file.read()

    words: list[str] = re.findall(r"\b\w+\b", text.lower())
    word_count: int = len(words)

    comma_count: int = text.count(",")
    char_count_incl_ws: int = len(text)
    whitespace_count: int = sum(ch.isspace() for ch in text)

    punctuation_counts: dict[str, int] = {mark: text.count(mark) for mark in PUNCTUATION_MARKS}

    total_word_length: int = sum(len(word) for word in words)
    average_word_length: float = (total_word_length / word_count) if word_count else 0.0

    top_words: list[tuple[str, int]] = Counter(words).most_common(3)

    print("-" * 30)
    print(f"Word count: {word_count}")
    print(f"Commas used: {comma_count}")
    print(f"Character count (incl. whitespaces): {char_count_incl_ws}")
    print(f"Whitespace characters: {whitespace_count}")
    print("")
    print("Punctuation marks:")
    for mark in PUNCTUATION_MARKS:
        print(f" > {mark}: {punctuation_counts[mark]}")
    print("")
    print(f"Average word length: {average_word_length:.2f}")
    print("")
    print("Top 3 most used words:")
    for word, count in top_words:
        print(f" > {word}: {count}")
    print("-" * 30)


def main() -> None:
    analyse("sample.txt")


if __name__ == "__main__":
    main()
