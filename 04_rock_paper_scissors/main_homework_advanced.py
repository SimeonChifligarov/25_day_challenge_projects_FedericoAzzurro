import random
from typing import Dict

# Game symbols
SYMBOLS: Dict[str, str] = {
    "rock": "🪨",
    "paper": "📄",
    "scissors": "✂️",
}

WINNING_COMBINATIONS = {
    ("rock", "scissors"),
    ("paper", "rock"),
    ("scissors", "paper"),
}


def get_player_choice() -> str:
    """Prompt the player for a valid choice."""
    while True:
        choice = input(
            "Choose rock (🪨), paper (📄), scissors (✂️), or 'q' to quit: "
        ).strip().lower()

        if choice == "q":
            print("Thanks for playing! 👋")
            raise SystemExit

        if choice in SYMBOLS:
            return choice

        print("❌ Invalid choice. Please try again.\n")


def get_computer_choice() -> str:
    """Randomly select the computer's choice."""
    return random.choice(tuple(SYMBOLS))


def display_results(player: str, computer: str) -> None:
    """Display the choices and game result."""
    print("\nResults")
    print("-" * 16)
    print(f"You:      {SYMBOLS[player]}  {player}")
    print(f"Computer: {SYMBOLS[computer]}  {computer}")
    print("-" * 16)

    if player == computer:
        print("It's a tie! 🤝")
    elif (player, computer) in WINNING_COMBINATIONS:
        print(f"You won with {player}! 🎉")
    else:
        print("Computer wins! 🤖")

    print()


def main() -> None:
    """Run the game loop indefinitely."""
    print("🎮 Rock–Paper–Scissors Game 🎮\n")

    while True:
        player_choice = get_player_choice()
        computer_choice = get_computer_choice()
        display_results(player_choice, computer_choice)


if __name__ == "__main__":
    main()
