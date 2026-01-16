"""
Simple rule-based chatbot.

Homework:
1) Add your own custom responses to the bot.

Notes on style / best practices applied:
- Clear type hints and docstrings
- Constants for bot phrases
- Small, testable helper functions
- No unnecessary intermediate lists (use generator expressions)
- Date/time formatted for humans
- Main loop isolated in `main()` + `if __name__ == "__main__":`
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Final

# --- Bot messages (constants) -------------------------------------------------

MSG_HELLO: Final[str] = "Hello there!"
MSG_GOODBYE: Final[str] = "Talk to you later!"
MSG_FALLBACK: Final[str] = "Sorry... I can't answer that right now."
MSG_HELP: Final[str] = (
    "I can respond to: hello/hi, goodbye/bye, time, date, help, "
    "your name, a joke, and a simple mood check (happy/sad/stressed)."
)

BOT_NAME: Final[str] = "PyBot"


# --- Data model ---------------------------------------------------------------

@dataclass(frozen=True, slots=True)
class Intent:
    """A simple intent: if any of `terms` appears in the input, reply with `reply`."""
    terms: tuple[str, ...]
    reply: str


# --- Helpers ------------------------------------------------------------------

def normalize(text: str) -> str:
    """Normalize user input for matching."""
    return text.strip().lower()


def contains(terms: tuple[str, ...] | list[str], content: str) -> bool:
    """
    Return True if any term appears in the content.
    Matching is case-insensitive (expects `content` already normalized).
    """
    return any(term in content for term in terms)


def format_now_time() -> str:
    """Return current local time in a human-friendly format."""
    return datetime.now().strftime("%H:%M:%S")


def format_today_date() -> str:
    """Return today's date in a human-friendly format."""
    return datetime.now().strftime("%Y-%m-%d")


# --- Core logic ----------------------------------------------------------------

CUSTOM_INTENTS: Final[tuple[Intent, ...]] = (
    # Homework additions start here:
    Intent(terms=("help", "what can you do", "commands"), reply=MSG_HELP),
    Intent(terms=("your name", "who are you", "what are you"), reply=f"My name is {BOT_NAME}."),
    Intent(terms=("tell me a joke", "joke"),
           reply="Why do programmers confuse Halloween and Christmas? Because OCT 31 == DEC 25."),
    Intent(terms=("how are you", "how's it going"), reply="I'm doing great—thanks for asking!"),
    Intent(terms=("happy", "great", "awesome"), reply="Love that for you 😄"),
    Intent(terms=("sad", "down", "depressed"),
           reply="I'm sorry you're feeling that way. Want to talk about what's going on?"),
    Intent(terms=("stressed", "anxious", "overwhelmed"),
           reply="That sounds heavy. Try 3 slow breaths—inhale 4, hold 2, exhale 6."),
    Intent(terms=("thanks", "thank you", "thx"), reply="You're welcome!"),
    # Homework additions end here.
)


def response(text: str) -> str:
    """Return the bot response for a given user input."""
    text = normalize(text)

    if contains(("hello", "hi", "hey"), text):
        return MSG_HELLO

    if contains(("goodbye", "bye", "see you"), text):
        return MSG_GOODBYE

    if contains(("what time is it", "current time", "time"), text):
        return f"The time is: {format_now_time()}"

    # Added: date intent
    if contains(("what date is it", "today's date", "date"), text):
        return f"Today's date is: {format_today_date()}"

    # Added: custom intents (homework)
    for intent in CUSTOM_INTENTS:
        if contains(intent.terms, text):
            return intent.reply

    return MSG_FALLBACK


def main() -> None:
    """Run the chatbot REPL."""
    while True:
        user_input = input("You: ")
        print(f"Bot: {response(user_input)}")


if __name__ == "__main__":
    main()
