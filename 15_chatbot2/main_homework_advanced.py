from __future__ import annotations

from datetime import datetime


def contains(terms: list[str], content: str) -> bool:
    content = content.lower()
    return any(term in content for term in terms)


def is_yes(text: str) -> bool:
    return contains(["yes", "yep", "yeah", "sure", "ok", "okay"], text)


def is_no(text: str) -> bool:
    return contains(["no", "nope", "nah"], text)


class ChatBot:
    def __init__(self, name: str) -> None:
        self.name = name
        self.history: list[str] = []
        self.pending_follow_up: str | None = None  # what the bot asked last (if anything)

    def response(self, text: str) -> str:
        text = text.strip().lower()

        # ----- follow-ups that depend on what the bot asked previously -----
        if self.pending_follow_up == "weather_tomorrow":
            self.pending_follow_up = None
            if is_yes(text):
                return "Tomorrow looks sunny with a high of 25 °C."
            if is_no(text):
                return "Alright — ask anytime."
            self.pending_follow_up = "weather_tomorrow"
            return "Please answer yes or no — would you like tomorrow's forecast too?"

        if self.pending_follow_up == "time_date":
            self.pending_follow_up = None
            if is_yes(text):
                return f"Today's date is: {datetime.now().strftime('%Y-%m-%d')}."
            if is_no(text):
                return "Got it."
            self.pending_follow_up = "time_date"
            return "Please answer yes or no — do you want today's date too?"

        if self.pending_follow_up == "ask_name":
            self.pending_follow_up = None
            # simplest name capture: take the whole message as their name
            user_name = text.title() if text else "there"
            return f"Nice to meet you, {user_name}!"

        # ----- follow-ups that depend on chat history (last user message) -----
        if "tomorrow" in text and self.history and "weather" in self.history[-1]:
            return "Tomorrow looks sunny with a high of 25 °C."

        # ----- normal intents -----
        if contains(["hello", "hi"], text):
            self.pending_follow_up = "ask_name"
            return "Hello there! What's your name?"

        if contains(["goodbye", "bye"], text):
            return "Talk to you later!"

        if contains(["what time is it", "current time"], text):
            self.pending_follow_up = "time_date"
            return f"The time is: {datetime.now().strftime('%H:%M:%S')}. Want today's date too? (yes/no)"

        if contains(["weather"], text):
            self.pending_follow_up = "weather_tomorrow"
            return "It’s partly cloudy and 22 °C right now. Want tomorrow too? (yes/no)"

        if contains(["help", "commands"], text):
            return (
                "I understand: hello/hi, goodbye/bye, what time is it/current time, weather, "
                "tomorrow (after weather), and help/commands."
            )

        return "Sorry... I can't answer that right now."

    def remember(self, text: str) -> None:
        self.history.append(text.strip().lower())
        if len(self.history) > 2:
            self.history.pop(0)

    def run(self) -> None:
        print("Type 'help' for commands. Type 'bye' to quit.\n")
        while True:
            user_input = input("You: ")
            bot_reply = self.response(user_input)
            print(f"{self.name}: {bot_reply}")

            if contains(["bye", "goodbye"], user_input):
                break

            self.remember(user_input)


def main() -> None:
    bot = ChatBot("Bob")
    bot.run()


if __name__ == "__main__":
    main()
