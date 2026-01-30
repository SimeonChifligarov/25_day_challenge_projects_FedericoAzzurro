import random
import sys
import time


class SlotMachine:
    def __init__(self, credits: int) -> None:
        self.credits = credits
        # Added a 4th symbol (optional homework #2)
        self.symbols: dict[str, int] = {
            "🍒": 1,
            "🍊": 2,
            "🍋": 5,
            "⭐": 10,
        }

    def spin(self, bet: int) -> None:
        if bet <= 0:
            print("Bet must be greater than 0...")
            return

        if self.credits < bet:
            print("Not enough credits...")
            return

        self.update_credits(-bet)

        result: list[str] = []
        for _ in range(3):
            time.sleep(0.2)
            landed = random.choice(list(self.symbols))
            print(landed, end="", flush=True)
            result.append(landed)

        print()

        winnings = self.calculate_winnings(result, bet)
        print(f"Credits won: {winnings}")

        self.update_credits(winnings)

        if self.credits == 0:
            print("Game over!")
            sys.exit()

        print(f"Credits remaining: {self.credits}")
        print("-" * 30)

    def calculate_winnings(self, result: list[str], bet: int) -> int:
        # Homework #1:
        # - Award credits for 2 in a row ONLY if the first two match.
        # - 3 in a row still wins more.
        first, second, third = result

        if first != second:
            return 0

        if second == third:
            # 3 in a row
            return self.symbols[first] * 3 * bet

        # 2 in a row (first two only)
        return self.symbols[first] * 2 * bet

    def update_credits(self, amount: int) -> None:
        self.credits += amount

    def play(self) -> None:
        print(f"Starting credits: {self.credits}")
        print("-" * 30)

        while True:
            try:
                bet = int(input("Bet: "))
            except ValueError:
                print("Please enter a valid number...")
                continue

            self.spin(bet)


def main() -> None:
    SlotMachine(200).play()


if __name__ == "__main__":
    main()
