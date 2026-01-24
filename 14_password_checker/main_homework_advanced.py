import string
from dataclasses import dataclass


@dataclass(frozen=True)
class PasswordReport:
    rating: str
    missing: list[str]
    warnings: list[str]


class PasswordValidator:
    def __init__(self, common_passwords_path: str = "common_passwords.txt") -> None:
        self.common_passwords: set[str] = self.load_common_passwords(common_passwords_path)

    @staticmethod
    def load_common_passwords(path: str) -> set[str]:
        """Load common passwords from a file; if missing, disable common-password checks."""
        try:
            with open(path, "r", encoding="utf-8") as file:
                return {line.strip() for line in file if line.strip()}
        except FileNotFoundError:
            print(f"⚠️ Warning: '{path}' not found. Common-password checks are disabled.")
            return set()

    def is_common(self, password: str) -> bool:
        """
        Check against the common list using raw and casefolded variants.
        (Casefold is stronger than lower() for Unicode.)
        """
        if not self.common_passwords:
            return False
        p = password.strip()
        return p in self.common_passwords or p.casefold() in self.common_passwords

    @staticmethod
    def has_upper(password: str) -> bool:
        return any(c.isupper() for c in password)

    @staticmethod
    def has_symbol(password: str) -> bool:
        return any(c in string.punctuation for c in password)

    @staticmethod
    def has_digit(password: str) -> bool:
        return any(c.isdigit() for c in password)

    @staticmethod
    def long_enough(password: str, min_len: int = 10) -> bool:
        return len(password) >= min_len

    @staticmethod
    def has_too_many_repeated(password: str, run_len: int = 3) -> bool:
        """Detect repeated characters in a row like 'aaa', '111'."""
        if run_len <= 1:
            return False

        streak = 1
        for i in range(1, len(password)):
            if password[i] == password[i - 1]:
                streak += 1
                if streak >= run_len:
                    return True
            else:
                streak = 1
        return False

    @staticmethod
    def has_straight_sequence(password: str, run_len: int = 3) -> bool:
        """Detect straight sequences like 'abc', '123', 'cba', '987'."""
        if len(password) < run_len:
            return False

        def step(a: str, b: str) -> int | None:
            if a.isdigit() and b.isdigit():
                return ord(b) - ord(a)
            if a.isalpha() and b.isalpha():
                return ord(b.casefold()) - ord(a.casefold())
            return None

        streak = 1
        last_step: int | None = None

        for i in range(1, len(password)):
            s = step(password[i - 1], password[i])
            if s in (1, -1) and s == last_step:
                streak += 1
                if streak >= run_len:
                    return True
            else:
                streak = 1
            last_step = s

        return False

    def report(self, password: str) -> PasswordReport:
        """Return rating plus actionable feedback (missing requirements + warnings)."""
        password = password.strip()
        warnings: list[str] = []

        if self.has_too_many_repeated(password, run_len=3):
            warnings.append("Too many repeated characters in a row (e.g. 'aaa', '111').")

        if self.has_straight_sequence(password, run_len=3):
            warnings.append("Contains a straight sequence (e.g. 'abc', '123', 'cba').")

        # If common, don't provide a detailed checklist (avoid helping attackers).
        if self.is_common(password):
            warnings.append("This password is very common. Choose something less predictable.")
            return PasswordReport(rating="poor", missing=[], warnings=warnings)

        checks = {
            "an uppercase letter (A-Z)": self.has_upper(password),
            "a symbol (e.g. !, @, #)": self.has_symbol(password),
            "a digit (0-9)": self.has_digit(password),
            "at least 10 characters": self.long_enough(password, min_len=10),
        }
        missing = [label for label, ok in checks.items() if not ok]

        # Thresholds are easy to change here.
        secure_min = len(checks)  # 4/4
        medium_min = len(checks) - 1  # 3/4

        score = sum(checks.values())
        if score >= secure_min:
            rating = "secure"
        elif score >= medium_min:
            rating = "medium"
        else:
            rating = "poor"

        return PasswordReport(rating=rating, missing=missing, warnings=warnings)


def main() -> None:
    # Link: https://github.com/danielmiessler/SecLists/blob/master/Passwords/Common-Credentials/10k-most-common.txt
    validator = PasswordValidator()

    print("🔒 Welcome to the Password Strength Checker!")
    print("Enter a password to get a quality rating. Type 'q' to quit.")

    while True:
        password = input("Enter password (or 'q' to quit): ").strip()

        if not password:
            print("Please enter a non-empty password.")
            continue

        if password.lower() in {"q", "quit", "exit"}:
            print("Goodbye! 👋")
            break

        report = validator.report(password)

        if report.rating == "secure":
            print("✅ Your password is secure!")
        elif report.rating == "medium":
            print("⚠️ Your password is of medium strength.")
        else:
            print("⚠️ Your password is weak.")

        if report.warnings:
            for w in report.warnings:
                print(f"• Warning: {w}")

        if report.missing:
            print("To make it stronger, add:")
            for item in report.missing:
                print(f"• {item}")
        else:
            # For common passwords we intentionally return missing=[]
            if report.rating != "poor" or not report.warnings:
                print("Nothing missing from the strength requirements!")


if __name__ == "__main__":
    main()
