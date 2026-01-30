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
        for s in result:
            time.sleep(0.2)
            print(s, end="", flush=True)
        print()
        return result

    def payout(self, result: list[str], bet: int) -> int:
        a, b, c = result
        if a != b:
            return 0
        if b == c:
            return self.symbols[a] * 3 * bet
        return self.symbols[a] * 2 * bet

    def spin(self, bet: int) -> bool:
        if bet <= 0:
            print("Bet must be greater than 0...")
            return True
        if bet > self.credits:
            print("Not enough credits...")
            return True

        self.credits -= bet
        result = self.spin_reels()
        won = self.payout(result, bet)
        print(f"Credits won: {won}")
        self.credits += won

        print(f"Credits remaining: {self.credits}")
        print("-" * 30)
        return self.credits > 0

    def play(self) -> None:
        print(f"Starting credits: {self.credits}")
        print("-" * 30)
        while self.credits > 0:
            raw = input("Bet (or 'q' to quit): ").strip().lower()
            if raw in {"q", "quit"}:
                break
            try:
                bet = int(raw)
            except ValueError:
                print("Please enter a valid number...")
                continue

            if not self.spin(bet):
                print("Game over!")


def main() -> None:
    symbols = {"🍒": 1, "🍊": 2, "🍋": 5, "⭐": 10}
    weights = [50, 35, 12, 3]  # ⭐ is rare
    SlotMachine(200, symbols, weights).play()


if __name__ == "__main__":
    main()
