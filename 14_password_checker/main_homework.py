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
        with open(path, "r", encoding="utf-8") as file:
            return {line.strip() for line in file if line.strip()}

    def is_common(self, password: str) -> bool:
        return password in self.common_passwords

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
    def has_too_many_sequential(password: str, run_len: int = 3) -> bool:
        """
        Detects repeated sequential characters like 'aaa', '111', '___' etc.
        (Same character repeated run_len times in a row.)
        """
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

    def report(self, password: str) -> PasswordReport:
        password = password.strip()

        missing: list[str] = []
        warnings: list[str] = []

        if self.is_common(password):
            warnings.append("This password is very common.")

        if self.has_too_many_sequential(password, run_len=3):
            warnings.append("Too many repeated characters in a row (e.g. 'aaa', '111').")

        checks = {
            "an uppercase letter (A-Z)": self.has_upper(password),
            "a symbol (e.g. !, @, #)": self.has_symbol(password),
            "a digit (0-9)": self.has_digit(password),  # NEW requirement for 'secure'
            "at least 10 characters": self.long_enough(password, min_len=10),
        }

        for label, ok in checks.items():
            if not ok:
                missing.append(label)

        # Rating:
        # - If common => poor (always)
        # - Else rating based on 4 checks: upper, symbol, digit, length
        #   secure: 4/4
        #   medium: 3/4
        #   poor: 0-2/4
        if self.is_common(password):
            rating = "poor"
        else:
            score = sum(checks.values())
            if score == 4:
                rating = "secure"
            elif score == 3:
                rating = "medium"
            else:
                rating = "poor"

        return PasswordReport(rating=rating, missing=missing, warnings=warnings)


def main() -> None:
    # Link: https://github.com/danielmiessler/SecLists/blob/master/Passwords/Common-Credentials/10k-most-common.txt
    validator = PasswordValidator()

    print("🔒 Welcome to the Password Strength Checker!")
    print("Enter a password to get a quality rating.")

    while True:
        password = input("Enter password: ").strip()
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
            print("Nothing missing from the strength requirements!")


if __name__ == "__main__":
    main()
