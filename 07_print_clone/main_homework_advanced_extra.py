from __future__ import annotations

from typing import Any, TextIO


def custom_print(
        *values: Any,
        sep: str | None = " ",
        end: str | None = "\n",
        caps: bool = False,
        include_types: bool = False,
        show_count: bool = False,
        enumerate_values: bool = False,
        repr_values: bool = False,  # improvement/new feature
        file: TextIO | None = None,  # print-compatible
        flush: bool = False,  # print-compatible
) -> None:
    """
    Print values with optional transformations and debug-friendly formatting.

    - caps: uppercases only string values
    - include_types: appends the type next to each printed value
    - show_count: adds a leading "(count=N)"
    - enumerate_values: prefixes each value with its index
    - repr_values: prints repr(value) instead of value (useful for debugging)
    """

    actual_sep = " " if sep is None else sep
    actual_end = "\n" if end is None else end

    output: list[Any] = []

    if show_count:
        output.append(f"(count={len(values)})")

    for idx, raw in enumerate(values):
        value = raw.upper() if caps and isinstance(raw, str) else raw
        display: Any = repr(value) if repr_values else value

        if enumerate_values:
            # Keep structure: label + value
            output.append(f"[{idx}]")
            output.append(display)
        else:
            output.append(display)

        if include_types:
            output.append(type(raw))

    print(*output, sep=actual_sep, end=actual_end, file=file, flush=flush)


# Examples
custom_print(
    "Alice\nBob",
    "Charlie",
    42,
    {"x": 1},
    caps=True,
    include_types=True,
    show_count=True,
    enumerate_values=True,
    repr_values=True,
    sep=" | ",
    end=" <END>\n",
    flush=True,
)
