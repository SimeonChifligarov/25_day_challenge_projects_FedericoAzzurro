from __future__ import annotations

import random
import time
from dataclasses import dataclass
from typing import Mapping, Protocol, Sequence


# -----------------------------
# Domain model
# -----------------------------


@dataclass(frozen=True)
class Symbol:
    glyph: str
    value: int
    weight: int


@dataclass(frozen=True)
class SpinResult:
    reels: tuple[str, ...]


@dataclass(frozen=True)
class Payout:
    amount: int
    reason: str


class PayoutRule(Protocol):
    def evaluate(self, result: SpinResult, bet: int) -> Payout: ...


@dataclass(frozen=True)
class FirstTwoMatchRule:
    """
    Awards credits if:
      - reels[0] == reels[1] -> 2-of-a-kind payout
      - reels[0] == reels[1] == reels[2] -> 3-of-a-kind payout

    Credits are only awarded for a 2-of-a-kind if the FIRST TWO reels match.
    """

    paytable: Mapping[str, int]
    two_kind_multiplier: int = 2
    three_kind_multiplier: int = 3

    def evaluate(self, result: SpinResult, bet: int) -> Payout:
        reels = result.reels
        if len(reels) < 2:
            return Payout(0, "no payout")

        if reels[0] != reels[1]:
            return Payout(0, "no payout")

        symbol = reels[0]
        base = self.paytable.get(symbol, 0)

        if len(reels) >= 3 and reels[1] == reels[2]:
            amount = base * self.three_kind_multiplier * bet
            return Payout(amount, "3 in a row")

        amount = base * self.two_kind_multiplier * bet
        return Payout(amount, "first two match")


# -----------------------------
# IO abstraction (testable design)
# -----------------------------


class IO(Protocol):
    def input(self, prompt: str) -> str: ...

    def output(self, text: str) -> None: ...


@dataclass
class ConsoleIO:
    def input(self, prompt: str) -> str:
        return input(prompt)

    def output(self, text: str) -> None:
        print(text)


# -----------------------------
# Engine
# -----------------------------


@dataclass(frozen=True)
class SlotMachineConfig:
    starting_credits: int = 200
    reels: int = 3
    spin_delay_s: float = 0.2


class SlotMachine:
    def __init__(
            self,
            config: SlotMachineConfig,
            symbols: Sequence[Symbol],
            payout_rule: PayoutRule,
            io: IO | None = None,
            rng: random.Random | None = None,
    ) -> None:
        if config.reels < 3:
            raise ValueError("This machine expects at least 3 reels.")
        if not symbols:
            raise ValueError("At least one symbol is required.")

        self._config = config
        self._io = io or ConsoleIO()
        self._rng = rng or random.Random()

        self._symbols = tuple(symbols)
        self._weights = [s.weight for s in self._symbols]
        self._glyphs = [s.glyph for s in self._symbols]

        self._payout_rule = payout_rule
        self._credits = config.starting_credits

    @property
    def credits(self) -> int:
        return self._credits

    def add_credits(self, amount: int) -> None:
        if amount <= 0:
            self._io.output("Amount must be greater than 0...")
            return
        self._credits += amount
        self._io.output(f"Credits added: {amount}")
        self._io.output(f"Credits remaining: {self._credits}")
        self._io.output("-" * 30)

    def spin(self, bet: int) -> None:
        if bet <= 0:
            self._io.output("Bet must be greater than 0...")
            return
        if bet > self._credits:
            self._io.output("Not enough credits...")
            return

        self._credits -= bet

        result = self._spin_reels()
        payout = self._payout_rule.evaluate(result, bet)

        self._io.output(f"Payout: {payout.amount} ({payout.reason})")
        self._credits += payout.amount
        self._io.output(f"Credits remaining: {self._credits}")
        self._io.output("-" * 30)

    def _spin_reels(self) -> SpinResult:
        """
        Bugfix #1:
        - Print the spin result INLINE on a single line.
        - Do not mix multiple output pathways or re-print results.
        """
        reels = self._rng.choices(
            self._glyphs,
            weights=self._weights,
            k=self._config.reels,
        )

        for glyph in reels:
            time.sleep(self._config.spin_delay_s)
            print(glyph, end="", flush=True)
        print()

        return SpinResult(tuple(reels))


# -----------------------------
# CLI / App layer
# -----------------------------


BET_PROMPT = "Bet, +amount to add credits (or 'q' to quit): "
EMPTY_CREDITS_PROMPT = "Out of credits. Add more (+amount) or quit (q): "


def _parse_add_command(text: str) -> int | None:
    """
    Returns amount if command is like '+123', otherwise None.
    """
    if not text.startswith("+"):
        return None
    try:
        return int(text[1:])
    except ValueError:
        return None


def run_game(machine: SlotMachine, io: IO) -> None:
    io.output(f"Starting credits: {machine.credits}")
    io.output("-" * 30)

    while True:
        if machine.credits == 0:
            raw = io.input(EMPTY_CREDITS_PROMPT).strip().lower()
            if raw in {"q", "quit"}:
                io.output("Goodbye!")
                return

            amount = _parse_add_command(raw)
            if amount is None:
                io.output("Invalid choice...")
                continue

            machine.add_credits(amount)
            continue

        # Bugfix #2: prompt clearly includes "+amount"
        raw = io.input(BET_PROMPT).strip().lower()
        if raw in {"q", "quit"}:
            io.output("Goodbye!")
            return

        amount = _parse_add_command(raw)
        if amount is not None:
            machine.add_credits(amount)
            continue

        try:
            bet = int(raw)
        except ValueError:
            io.output("Please enter a valid number...")
            continue

        machine.spin(bet)


def main() -> None:
    config = SlotMachineConfig(starting_credits=200, reels=3, spin_delay_s=0.2)

    # Includes a 4th symbol and weighted odds.
    symbols = [
        Symbol("🍒", value=1, weight=50),
        Symbol("🍊", value=2, weight=35),
        Symbol("🍋", value=5, weight=12),
        Symbol("⭐", value=10, weight=3),
    ]

    paytable: dict[str, int] = {s.glyph: s.value for s in symbols}
    payout_rule = FirstTwoMatchRule(paytable=paytable)

    io = ConsoleIO()
    machine = SlotMachine(config=config, symbols=symbols, payout_rule=payout_rule, io=io)

    run_game(machine, io)


if __name__ == "__main__":
    main()
