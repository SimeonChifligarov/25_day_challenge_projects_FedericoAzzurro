from __future__ import annotations

from datetime import datetime

# Intent terms (centralized)
HELLO = ["hello", "hi"]
BYE = ["goodbye", "bye"]
TIME = ["what time is it", "current time", "time"]
WEATHER = ["weather"]
HELP = ["help", "commands"]


# 1. Helper methods
def contains(terms: list[str], content_lower: str) -> bool:
    # NOTE: expects already-lowercased content
    return any(term in content_lower for term in terms)


def words(text_lower: str) -> set[str]:
    # simplest tokenization: split on whitespace
    return set(text_lower.split())


def is_yes(text_lower: str) -> bool:
    return bool(words(text_lower) & {"yes", "y", "yeah", "yep", "sure", "ok", "okay"})


def is_no(text_lower: str) -> bool:
    return bool(words(text_lower) & {"no", "n", "nope", "nah"})


def extract_name(text_lower: str) -> str | None:
    """
    Very small name extractor:
    - "i'm alex" / "im alex"
    - "my name is alex"
    Otherwise: None (caller may fallback).
    """
    t = text_lower.strip()

    for prefix in ("i'm ", "im "):
        if t.startswith(prefix) and len(t) > len(prefix):
            return t[len(prefix):].strip().title()

    if "my name is " in t:
        after = t.split("my name is ", 1)[1].strip()
        if after:
            return after.title()

    return None


# 2. Chatbot class
class ChatBot:
    def __init__(self, name: str) -> None:
        self.name = name
        self.history: list[tuple[str, str]] = []  # (speaker: "user"|"bot", text_lower)
        self.pending: dict[str, object] = {"type": None, "tries": 0}  # small state

    def remember(self, speaker: str, text_lower: str) -> None:
        self.history.append((speaker, text_lower))
        if len(self.history) > 6:
            self.history.pop(0)

    def last(self, speaker: str) -> str:
        for who, msg in reversed(self.history):
            if who == speaker:
                return msg
        return ""

    def yes_no(
            self,
            text_lower: str,
            *,
            key: str,
            on_yes: str,
            on_no: str,
            question: str,
            max_tries: int = 2,
    ) -> str:
        if is_yes(text_lower):
            self.pending["type"] = None
            self.pending["tries"] = 0
            return on_yes

        if is_no(text_lower):
            self.pending["type"] = None
            self.pending["tries"] = 0
            return on_no

        tries = int(self.pending.get("tries", 0)) + 1
        self.pending["type"] = key
        self.pending["tries"] = tries

        if tries >= max_tries:
            self.pending["type"] = None
            self.pending["tries"] = 0
            return "No worries — let's continue. (Tip: reply with yes/no for follow-ups.)"

        return question

    # 3. Response functionality
    def response(self, text: str) -> str:
        text_lower = text.strip().lower()

        # 9) Empty input safety
        if not text_lower:
            return "Say something and I'll do my best to help 🙂"

        now = datetime.now()

        # ----- follow-ups based on structured state/history -----
        if self.pending["type"] == "weather_tomorrow":
            return self.yes_no(
                text_lower,
                key="weather_tomorrow",
                on_yes="Tomorrow looks sunny with a high of 25 °C.",
                on_no="Alright — ask anytime.",
                question="Would you like tomorrow's forecast too? (yes/no)",
            )

        if self.pending["type"] == "time_date":
            return self.yes_no(
                text_lower,
                key="time_date",
                on_yes=f"Today's date is: {now:%Y-%m-%d}.",
                on_no="Got it.",
                question="Do you want today's date too? (yes/no)",
            )

        if self.pending["type"] == "ask_name":
            name = extract_name(text_lower) or text_lower.title()
            self.pending["type"] = None
            self.pending["tries"] = 0
            return f"Nice to meet you, {name}!"

        # 2) History-based follow-up (user says "tomorrow" after weather)
        last_user = self.last("user")
        if contains(["tomorrow"], text_lower) and contains(WEATHER, last_user):
            return "Tomorrow looks sunny with a high of 25 °C."

        # ----- normal intents -----
        if contains(HELLO, text_lower):
            self.pending["type"] = "ask_name"
            self.pending["tries"] = 0
            return "Hello there! What's your name?"

        if contains(BYE, text_lower):
            return "Talk to you later!"

        if contains(TIME, text_lower):
            self.pending["type"] = "time_date"
            self.pending["tries"] = 0
            return f"The time is: {now:%H:%M:%S}. Want today's date too? (yes/no)"

        if contains(WEATHER, text_lower):
            self.pending["type"] = "weather_tomorrow"
            self.pending["tries"] = 0
            return "It’s partly cloudy and 22 °C right now. Want tomorrow too? (yes/no)"

        if contains(HELP, text_lower):
            return (
                "I understand: hello/hi, goodbye/bye, what time is it/current time/time, "
                "weather, tomorrow (after weather), and help/commands."
            )

        return "Sorry... I can't answer that right now."

    # 5. Run the bot
    def run(self) -> None:
        print("Type 'help' for commands. Type 'bye' to quit.\n")
        while True:
            user_input = input("You: ")
            bot_reply = self.response(user_input)
            print(f"{self.name}: {bot_reply}")

            # remember both sides (structured history)
            user_lower = user_input.strip().lower()
            self.remember("user", user_lower)
            self.remember("bot", bot_reply.strip().lower())

            if contains(BYE, user_lower):
                break


def main() -> None:
    bot = ChatBot("Bob")
    bot.run()


if __name__ == "__main__":
    main()
