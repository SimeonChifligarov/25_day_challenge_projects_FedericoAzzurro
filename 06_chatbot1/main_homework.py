from __future__ import annotations

from datetime import datetime


def contains(terms: list[str], content: str) -> bool:
    """Return True if any term appears in the content (case-insensitive)."""
    content = content.lower()
    return any(term in content for term in terms)


def response(text: str) -> str:
    """Pick an appropriate bot response based on the user's text."""
    text = text.lower()

    if contains(["hello", "hi"], text):
        return "Hello there!"
    if contains(["goodbye", "bye"], text):
        return "Talk to you later!"
    if contains(["what time is it", "current time"], text):
        return f"The time is: {datetime.now()}"

    # Custom responses (homework)
    if contains(["how are you", "how r u"], text):
        return "I'm doing great—thanks for asking!"
    if contains(["your name", "who are you"], text):
        return "I'm a tiny Python bot 🤖"
    if contains(["help", "commands", "what can you do"], text):
        return "Try: hi, bye, time, how are you, your name."

    # New custom responses
    if contains(["thank you", "thanks"], text):
        return "You're welcome!"
    if contains(["joke"], text):
        return "Why do programmers prefer dark mode? Because light attracts bugs."
    if contains(["date", "today"], text):
        return f"Today's date is: {datetime.now().date()}"

    return "Sorry... I can't answer that right now."


def main() -> None:
    while True:
        user_input = input("You: ")
        print(f"Bot: {response(user_input)}")


if __name__ == "__main__":
    main()
