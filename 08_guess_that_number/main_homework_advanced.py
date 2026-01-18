from typing import Final
import random

# Game configuration
LOWER_LIMIT: Final[int] = 0
UPPER_LIMIT: Final[int] = 100

# Commands
QUIT_COMMANDS: Final[set[str]] = {"q", "quit", "exit"}
YES_ANSWERS: Final[set[str]] = {"y", "yes"}


def bot_message(msg: str) -> None:
    """Prints a formatted message from the bot."""
    print(f"Bot: {msg}")


def ask_to_play_again() -> bool:
    """Asks the user if they want to play again."""
    answer: str = input("You (play again? y/n): ").strip().lower()
    return answer in YES_ANSWERS


def read_guess() -> int | None:
    """
    Reads a guess from the user.
    Returns:
        - int if a valid number was provided
        - None if the user wants to quit
    """
    raw: str = input("You: ").strip().lower()

    if raw in QUIT_COMMANDS:
        return None

    try:
        return int(raw)
    except ValueError as error:
        bot_message(f"{error}. Please only use numbers (or type 'q' to quit).")
        return -1  # sentinel for "invalid guess"


def play_round() -> None:
    """Plays a single round of the game."""
    random_number: int = random.randint(LOWER_LIMIT, UPPER_LIMIT)
    tries: int = 0

    bot_message(f"Guess a number between {LOWER_LIMIT} & {UPPER_LIMIT}.")
    bot_message("Type 'q' to quit.")

    while True:
        guess: int | None = read_guess()

        if guess is None:
            bot_message("Goodbye!")
            return

        if guess == -1:
            # Invalid input (not a number), do not count as a try
            continue

        if not (LOWER_LIMIT <= guess <= UPPER_LIMIT):
            bot_message(f"Please guess within the range {LOWER_LIMIT} to {UPPER_LIMIT}.")
            continue

        tries += 1

        if guess > random_number:
            bot_message("The number is lower.")
        elif guess < random_number:
            bot_message("The number is higher.")
        else:
            bot_message("You guessed correctly! You win!")
            bot_message(f"It took you {tries} tries.")
            return


def main() -> None:
    """Runs the Guess That Number game with replay support."""
    bot_message("Welcome to GuessThatNumber™!")

    while True:
        play_round()
        if not ask_to_play_again():
            bot_message("Thanks for playing!")
            break


if __name__ == "__main__":
    main()
