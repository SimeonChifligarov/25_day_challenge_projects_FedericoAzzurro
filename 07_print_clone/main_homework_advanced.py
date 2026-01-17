from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class _PrintItem:
    """Internal representation of one printed item."""
    display: Any
    value_type: type[Any]


def custom_print(
        *values: Any,
        sep: str | None = " ",
        end: str | None = "\n",
        caps: bool = False,
        include_types: bool = False,
        show_count: bool = False,  # Homework #1
        enumerate_values: bool = False,  # Homework #2 (my feature)
) -> None:
    """
    Print values with optional transformations.

    Args:
        values: Values to print.
        sep: Separator between printed values (None -> default " ").
        end: Line ending (None -> default "\\n").
        caps: Uppercase all string values.
        include_types: Print each value along with its type.
        show_count: Include the number of input values being printed.
        enumerate_values: Prefix each value with its index (0-based).
    """
    # Match print() behavior when sep/end are None.
    actual_sep = " " if sep is None else sep
    actual_end = "\n" if end is None else end

    # Transform values (caps) while keeping original types for include_types.
    processed_values: list[Any] = [
        value.upper() if caps and isinstance(value, str) else value
        for value in values
    ]

    items: list[_PrintItem] = []
    for idx, value in enumerate(processed_values):
        display: Any = f"{idx}: {value}" if enumerate_values else value
        items.append(_PrintItem(display=display, value_type=type(value)))

    output: list[Any] = []

    if show_count:
        output.append(f"(count={len(values)})")

    if include_types:
        output.extend((item.display, item.value_type) for item in items)
    else:
        output.extend(item.display for item in items)

    print(*output, sep=actual_sep, end=actual_end)


# Original examples (still work)
custom_print("Bob", "James", 10, caps=False, include_types=False, sep=", ")
custom_print("Bob", "James", 10, caps=True, include_types=False, sep=", ", end="!\n")
custom_print("Bob", "James", 10, include_types=True, sep=", ", end="!\n")
custom_print([], include_types=True, sep=", ", end="!\n")

# New features
custom_print("Bob", "James", 10, show_count=True, sep=", ")
custom_print("Bob", "James", 10, show_count=True, enumerate_values=True, caps=True, sep=" | ")
custom_print("Bob", "James", 10, show_count=True, enumerate_values=True, include_types=True, sep=" / ")
