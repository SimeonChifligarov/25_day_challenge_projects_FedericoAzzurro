from datetime import datetime

"""
V2: Added history to chats and took an OOP approach
"""


# 1. Create a helper method for recognising terms
def contains(terms: list[str], content: str) -> bool:
    matches: list[bool] = []
    for term in terms:
        matches.append(term in content.lower())
    return any(matches)


# 2. Create the chatbot class
class ChatBot:
    def __init__(self, name: str) -> None:
        self.history: list[str] = []
        self.name = name

    # 3. Code the response functionality
    def response(self, text: str) -> str:
        text = text.lower()
        last: str = self.history[-1] if self.history else ""

        # follow-ups using chat history
        if contains(["tomorrow"], text) and contains(["weather"], last):
            return "Tomorrow looks sunny with a high of 25 °C."
        if contains(["and you", "how about you"], text) and contains(["hi", "hello"], last):
            return "I'm doing great, thanks! 🙂"
        if contains(["what about"], text) and contains(["time"], last):
            return f"Still the same idea 🙂 Current time: {datetime.now().strftime('%H:%M:%S')}"

        # normal intents
        if contains(["hello", "hi"], text):
            return "Hello there!"
        elif contains(["goodbye", "bye"], text):
            return "Talk to you later!"
        elif contains(["what time is it", "current time", "time"], text):
            return f"The time is: {datetime.now().strftime('%H:%M:%S')}"
        elif contains(["weather"], text):
            return "It’s partly cloudy and 22 °C right now."
        elif contains(["help", "commands"], text):
            return (
                "I understand: hello/hi, goodbye/bye, what time is it/current time/time, "
                "weather, tomorrow (after weather), 'and you' (after hello), "
                "'what about' (after time), and help/commands."
            )

        return "Sorry... I can't answer that right now."

    # 4. Add memory to the bot
    def remember(self, text: str) -> None:
        self.history.append(text.lower())
        if len(self.history) > 2:
            # keep only most-recent 2 messages
            self.history.pop(0)

    # 5. Run the bot
    def run(self) -> None:
        print("Type 'help' for commands. Type 'bye' to quit.\n")
        while True:
            user_input: str = input("You: ")
            bot_reply: str = self.response(user_input)
            print(f"{self.name}: {bot_reply}")

            # exit if user said goodbye
            if contains(["bye", "goodbye"], user_input):
                break

            # remember after responding
            self.remember(user_input)


def main() -> None:
    bot: ChatBot = ChatBot("Bob")
    bot.run()


if __name__ == "__main__":
    main()
