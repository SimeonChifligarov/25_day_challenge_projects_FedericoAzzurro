from __future__ import annotations

from typing import Any


def custom_print(
        *values: Any,
        sep: str | None = " ",
        end: str | None = "\n",
        caps: bool = False,
        include_types: bool = False,
        include_count: bool = False,  # Homework 1
        prefix: str | None = None,  # Homework 2 (my feature)
) -> None:
    # Feature: optional prefix printed before everything else
    items: list[Any] = []
    if prefix is not None:
        items.append(prefix)

    # Homework 1: count how many positional values were provided
    if include_count:
        items.append(f"[count={len(values)}]")

    # Uppercase all string values if flag is toggled
    processed: list[Any] = []
    for value in values:
        if caps and isinstance(value, str):
            processed.append(value.upper())
        else:
            processed.append(value)

    # Includes type of every argument if flag is toggled
    if include_types:
        processed = [(v, type(v)) for v in processed]

    items.extend(processed)
    print(*items, sep=sep, end=end)


# Examples
custom_print("Bob", "James", 10, caps=False, include_types=False, sep=", ")
custom_print("Bob", "James", 10, caps=True, include_types=False, sep=", ", end="!\n")
custom_print("Bob", "James", 10, include_types=True, sep=", ", end="!\n")
custom_print([], include_types=True, sep=", ", end="!\n")

# Homework examples
custom_print("Bob", "James", 10, include_count=True, sep=", ")
custom_print("Bob", "James", 10, include_count=True, prefix=">>>", sep=", ", end="!\n")
