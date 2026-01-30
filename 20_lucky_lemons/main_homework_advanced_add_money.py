import random
import time
from dataclasses import dataclass
from typing import Mapping


@dataclass
class SlotMachine:
    credits: int
    symbols: Mapping[str, int]
    weights: list[int]
    rng: random.Random = random.Random()

    def spin_reels(self) -> list[str]:
        reel_symbols = list(self.symbols)
        result = self.rng.choices(reel_symbols, weights=self.weights, k=3)
        for symbol in result:
            time.sleep(0.2)
            print(symbol, end="", flush=True)
        print()
        return result

    def payout(self, result: list[str], bet: int) -> int:
        a, b, c = result
        if a != b:
            return 0
        if b == c:
            return self.symbols[a] * 3 * bet
        return self.symbols[a] * 2 * bet

    def add_credits(self, amount: int) -> None:
        if amount <= 0:
            print("Amount must be greater than 0...")
            return
        self.credits += amount
        print(f"Credits added: {amount}")
        print(f"Credits remaining: {self.credits}")
        print("-" * 30)

    def spin(self, bet: int) -> None:
        if bet <= 0:
            print("Bet must be greater than 0...")
            return
        if bet > self.credits:
            print("Not enough credits...")
            return

        self.credits -= bet
        result = self.spin_reels()
        winnings = self.payout(result, bet)

        print(f"Credits won: {winnings}")
        self.credits += winnings
        print(f"Credits remaining: {self.credits}")
        print("-" * 30)

    def play(self) -> None:
        print(f"Starting credits: {self.credits}")
        print("-" * 30)

        while True:
            # 🔴 Special case: out of credits
            if self.credits == 0:
                choice = input(
                    "Out of credits. Add more (+amount) or quit (q): "
                ).strip().lower()

                if choice in {"q", "quit"}:
                    print("Goodbye!")
                    break

                if choice.startswith("+"):
                    try:
                        amount = int(choice[1:])
                    except ValueError:
                        print("Invalid amount...")
                        continue
                    self.add_credits(amount)
                    continue

                print("Invalid choice...")
                continue

            command = input("Bet (or 'q' to quit): ").strip().lower()

            if command in {"q", "quit"}:
                print("Goodbye!")
                break

            try:
                bet = int(command)
            except ValueError:
                print("Please enter a valid number...")
                continue

            self.spin(bet)


def main() -> None:
    symbols = {"🍒": 1, "🍊": 2, "🍋": 5, "⭐": 10}
    weights = [50, 35, 12, 3]
    SlotMachine(200, symbols, weights).play()


if __name__ == "__main__":
    main()
