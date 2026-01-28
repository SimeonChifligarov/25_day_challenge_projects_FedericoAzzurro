from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import FrozenSet, Pattern, Tuple

_EMAIL_RE: Pattern[str] = re.compile(
    r"\b[A-Za-z0-9.!#$%&'*+/=?^_`{|}~-]+@"
    r"[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?"
    r"(?:\.[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?)*"
    r"\.[A-Za-z]{2,}\b"
)

_DEFAULT_POPULAR_DOMAINS: FrozenSet[str] = frozenset(
    {
        "gmail.com",
        "yahoo.com",
        "outlook.com",
        "hotmail.com",
        "icloud.com",
        "mail.com",
    }
)


@dataclass(frozen=True, slots=True)
class EmailExtractor:
    pattern: Pattern[str] = _EMAIL_RE
    popular_domains: FrozenSet[str] = _DEFAULT_POPULAR_DOMAINS

    def extract(
            self,
            text: str,
            *,
            unique_only: bool = True,
            case_sensitive: bool = True,
            popular_domains_only: bool = False,
    ) -> list[str]:
        emails: list[str] = self.pattern.findall(text)

        if not case_sensitive:
            emails = [e.lower() for e in emails]

        if popular_domains_only:
            emails = [e for e in emails if self._domain_of(e) in self.popular_domains]

        if unique_only:
            emails = self._unique_preserve_order(emails)

        return emails

    @staticmethod
    def _domain_of(email: str) -> str:
        # Domains are case-insensitive; normalize for robust filtering.
        return email.rsplit("@", 1)[1].lower()

    @staticmethod
    def _unique_preserve_order(items: list[str]) -> list[str]:
        # More explicit than dict.fromkeys, handles all hashable items.
        seen: set[str] = set()
        out: list[str] = []
        for item in items:
            if item in seen:
                continue
            seen.add(item)
            out.append(item)
        return out


def ask_bool(prompt: str, *, default: bool = False) -> bool:
    """
    Robust yes/no prompt with default.

    Accepts: y/yes/true/1 and n/no/false/0 (case-insensitive).
    Enter returns the default.
    """
    suffix = " [Y/n]: " if default else " [y/N]: "
    raw = input(prompt + suffix).strip().lower()

    if raw == "":
        return default
    if raw in {"y", "yes", "true", "1"}:
        return True
    if raw in {"n", "no", "false", "0"}:
        return False

    print("Please answer with y/n (or press Enter for default).")
    return ask_bool(prompt, default=default)


def read_text(path: Path) -> str:
    # errors="replace" makes it resilient for HTML / messy files.
    return path.read_text(encoding="utf-8", errors="replace")


def list_emails(path: Path, *, extractor: EmailExtractor, popular_only: bool) -> None:
    text = read_text(path)
    emails = extractor.extract(text, popular_domains_only=popular_only)

    print("\n".join(emails) if emails else "No emails found...")


def main() -> None:
    path = Path("file.txt")  # keep simple; can be changed if needed
    popular_only = ask_bool("Keep only popular email domains?", default=False)
    extractor = EmailExtractor()
    list_emails(path, extractor=extractor, popular_only=popular_only)


if __name__ == "__main__":
    main()
