import re

# Keep this small and easy to extend.
POPULAR_EMAIL_DOMAINS: set[str] = {
    "gmail.com",
    "yahoo.com",
    "outlook.com",
    "hotmail.com",
    "icloud.com",
    "mail.com",
}


def extract_emails(
        text: str,
        unique_only: bool = True,
        case_sensitive: bool = True,
        popular_domains_only: bool = False,
        popular_domains: set[str] | None = None,
) -> list[str]:
    email_pattern: str = (
        r"\b[A-Za-z0-9.!#$%&'*+/=?^_`{|}~-]+@"
        r"[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?"
        r"(?:\.[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?)*"
        r"\.[A-Za-z]{2,}\b"
    )

    emails: list[str] = re.findall(email_pattern, text)

    if not case_sensitive:
        emails = [email.lower() for email in emails]

    if popular_domains_only:
        allowed: set[str] = popular_domains or POPULAR_EMAIL_DOMAINS
        emails = [email for email in emails if email.split("@", 1)[1] in allowed]

    if unique_only:
        emails = list(dict.fromkeys(emails))

    return emails


def list_emails(path: str, popular_domains_only: bool = False) -> None:
    with open(path, "r", encoding="utf-8") as f:
        text: str = f.read()

    emails: list[str] = extract_emails(text, popular_domains_only=popular_domains_only)

    if emails:
        for email in emails:
            print(email)
    else:
        print("No emails found...")


def main() -> None:
    # Turn this on to keep only popular domains.
    list_emails("file.txt", popular_domains_only=True)


if __name__ == "__main__":
    main()
