from typing import Final
import random

# Game configuration (defaults; may be overridden by difficulty choice)
DEFAULT_LOWER_LIMIT: Final[int] = 0
DEFAULT_UPPER_LIMIT: Final[int] = 100

# Difficulties (simple presets)
DIFFICULTY_RANGES: Final[dict[str, tuple[int, int]]] = {
    "easy": (0, 50),
    "medium": (0, 100),
    "hard": (0, 500),
}

# Attempts
DEFAULT_MAX_ATTEMPTS: Final[int] = 10

# Commands / answers
QUIT_COMMANDS: Final[set[str]] = {"q", "quit", "exit"}
YES_ANSWERS: Final[set[str]] = {"y", "yes"}
NO_ANSWERS: Final[set[str]] = {"n", "no"}

# Secret/debug commands (kept simple)
REVEAL_COMMAND: Final[str] = "reveal"

# Encouragement messages (rotated randomly)
ENCOURAGEMENTS: Final[tuple[str, ...]] = (
    "Nice try!",
    "Keep going!",
    "You got this!",
    "Good effort!",
    "Don’t give up!",
)

# User-facing text (avoid magic strings)
PROMPT_GUESS: Final[str] = "You: "
PROMPT_PLAY_AGAIN: Final[str] = "You (play again? y/n): "
PROMPT_DIFFICULTY: Final[str] = "You (difficulty: easy/medium/hard): "
PROMPT_CONFIRM_EXTREME: Final[str] = "You (are you sure? y/n): "


def bot_message(msg: str) -> None:
    """Prints a formatted message from the bot."""
    print(f"Bot: {msg}")


def pluralize_tries(tries: int) -> str:
    """Returns a human-friendly tries string (e.g., '1 try', '2 tries')."""
    return f"{tries} try" if tries == 1 else f"{tries} tries"


def ask_yes_no(prompt: str) -> bool:
    """Asks a yes/no question; returns True for yes, False for no (keeps asking until valid)."""
    while True:
        answer: str = input(prompt).strip().lower()
        if answer in YES_ANSWERS:
            return True
        if answer in NO_ANSWERS:
            return False
        bot_message("Please answer with 'y' or 'n'.")


def choose_difficulty() -> tuple[int, int, str]:
    """Lets the user choose a difficulty and returns (lower, upper, label)."""
    bot_message("Choose a difficulty: easy / medium / hard")
    while True:
        choice: str = input(PROMPT_DIFFICULTY).strip().lower()

        if choice in QUIT_COMMANDS:
            return DEFAULT_LOWER_LIMIT, DEFAULT_UPPER_LIMIT, "medium"

        if choice in DIFFICULTY_RANGES:
            lower, upper = DIFFICULTY_RANGES[choice]
            return lower, upper, choice

        bot_message("Invalid difficulty. Please type: easy, medium, or hard (or 'q' to quit).")


def try_parse_int(raw: str) -> int | None:
    """
    Attempts to parse an integer from raw input.
    Returns:
        - int if parsed successfully
        - None if not an integer
    """
    try:
        return int(raw)
    except ValueError:
        return None


def get_guess(
        *,
        lower_limit: int,
        upper_limit: int,
        target: int,
) -> int | None:
    """
    Reads a guess from the user.
    Returns:
        - int: a valid guess (in range)
        - None: user wants to quit the round
    """
    raw: str = input(PROMPT_GUESS).strip()
    raw_lower: str = raw.lower()

    if raw_lower in QUIT_COMMANDS:
        return None

    # Cheat/debug command (simple)
    if raw_lower == REVEAL_COMMAND:
        bot_message(f"(cheat) The number is {target}.")
        return -1  # sentinel meaning "no guess was made"

    # Better float feedback (simple detection)
    if "." in raw or "," in raw:
        bot_message("Please enter a whole number (no decimals).")
        return -1

    parsed: int | None = try_parse_int(raw)
    if parsed is None:
        bot_message("That doesn't look like a number. Please enter an integer (or type 'q' to quit).")
        return -1

    # Range validation
    if not (lower_limit <= parsed <= upper_limit):
        bot_message(f"Please guess within the range {lower_limit} to {upper_limit}.")
        return -1

    # Optional confirmation for extreme values (simple)
    if parsed in {lower_limit, upper_limit}:
        bot_message("You picked an extreme value.")
        if not ask_yes_no(PROMPT_CONFIRM_EXTREME):
            bot_message("Okay—pick another number.")
            return -1

    return parsed


def give_hint(target: int) -> str:
    """
    Returns a simple hint string. (Used after a few attempts.)
    Non-complex hints: parity + broad half-range.
    """
    parity: str = "even" if target % 2 == 0 else "odd"
    half_hint: str = "above" if target > 0 else "at or below"

    # This "half_hint" is too generic if lower isn't always 0, so we keep it extremely simple:
    # We'll just give parity as the primary hint; it's always valid.
    return f"Hint: the number is {parity}."


def play_round(
        *,
        lower_limit: int,
        upper_limit: int,
        difficulty_label: str,
        max_attempts: int,
) -> int | None:
    """
    Plays a single round.
    Returns:
        - attempts_used (int) if the user finishes the round (win or loss)
        - None if the user quits mid-round
    """
    target: int = random.randint(lower_limit, upper_limit)
    tries: int = 0
    previous_guesses: set[int] = set()

    bot_message(f"Starting a {difficulty_label} round!")
    bot_message(f"Guess a number between {lower_limit} & {upper_limit}.")
    bot_message(f"You have {max_attempts} attempts. Type 'q' to quit. (Secret: type '{REVEAL_COMMAND}')")

    while True:
        remaining: int = max_attempts - tries
        bot_message(f"Attempts remaining: {remaining}")

        guess: int | None = get_guess(lower_limit=lower_limit, upper_limit=upper_limit, target=target)

        if guess is None:
            bot_message("Round ended (you quit).")
            return None

        if guess == -1:
            # No valid guess was made (invalid input or cheat reveal).
            continue

        if guess in previous_guesses:
            bot_message("You already guessed that number. Try a different one.")
            continue

        previous_guesses.add(guess)
        tries += 1

        # Simple encouragement after valid guess (not after every message)
        bot_message(random.choice(ENCOURAGEMENTS))

        if guess > target:
            bot_message("The number is lower.")
        elif guess < target:
            bot_message("The number is higher.")
        else:
            bot_message("You guessed correctly! You win!")
            bot_message(f"It took you {pluralize_tries(tries)}.")
            return tries

        # Hint after 5 tries (simple)
        if tries == 5:
            bot_message(give_hint(target))

        # Max attempts check
        if tries >= max_attempts:
            bot_message("No attempts left.")
            bot_message(f"You lost this round. The number was {target}.")
            return tries


def main() -> None:
    """Runs the Guess That Number game with simple stats and quality improvements."""
    # Session stats
    rounds_played: int = 0
    total_attempts_used: int = 0
    best_score: int | None = None

    bot_message("Welcome to GuessThatNumber™!")

    lower_limit, upper_limit, difficulty_label = choose_difficulty()
    max_attempts: int = DEFAULT_MAX_ATTEMPTS

    while True:
        result: int | None = play_round(
            lower_limit=lower_limit,
            upper_limit=upper_limit,
            difficulty_label=difficulty_label,
            max_attempts=max_attempts,
        )

        if result is None:
            # User quit mid-round: still allow them to decide to play again or stop.
            if not ask_yes_no(PROMPT_PLAY_AGAIN):
                bot_message("Thanks for playing!")
                break
            continue

        rounds_played += 1
        total_attempts_used += result

        if best_score is None or result < best_score:
            best_score = result
            bot_message(f"New best score: {pluralize_tries(best_score)}!")

        # Simple statistics (end-of-round)
        average_attempts: float = total_attempts_used / rounds_played
        bot_message(f"Rounds played: {rounds_played}")
        bot_message(f"Average attempts used: {average_attempts:.2f}")
        bot_message(f"Best score this session: {pluralize_tries(best_score)}")

        if not ask_yes_no(PROMPT_PLAY_AGAIN):
            bot_message("Thanks for playing!")
            break

        # Allow difficulty change between rounds (simple)
        if ask_yes_no("You (change difficulty? y/n): "):
            lower_limit, upper_limit, difficulty_label = choose_difficulty()


if __name__ == "__main__":
    main()
