from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import Dict, List, Tuple

Move = str


@dataclass
class GameStats:
    """Collects aggregate statistics across all matches played."""
    rounds_played: int = 0
    player_round_wins: int = 0
    computer_round_wins: int = 0
    ties: int = 0

    player_move_counts: Dict[Move, int] = field(default_factory=dict)
    computer_move_counts: Dict[Move, int] = field(default_factory=dict)

    match_played: int = 0
    player_match_wins: int = 0
    computer_match_wins: int = 0

    def record_moves(self, player: Move, computer: Move) -> None:
        self.player_move_counts[player] = self.player_move_counts.get(player, 0) + 1
        self.computer_move_counts[computer] = self.computer_move_counts.get(computer, 0) + 1

    def player_round_win_rate(self) -> float:
        decided = self.player_round_wins + self.computer_round_wins
        return (self.player_round_wins / decided) if decided else 0.0


class RockPaperScissorsGame:
    SYMBOLS: Dict[Move, str] = {
        "rock": "🪨",
        "paper": "📄",
        "scissors": "✂️",
    }

    WINNING_COMBINATIONS: set[Tuple[Move, Move]] = {
        ("rock", "scissors"),
        ("paper", "rock"),
        ("scissors", "paper"),
    }

    def __init__(self, best_of: int = 3) -> None:
        self.best_of = self._normalize_best_of(best_of)
        self.stats = GameStats()
        self._rng = random.Random()

    @staticmethod
    def _normalize_best_of(value: int) -> int:
        """
        Ensure best_of is a positive odd integer >= 1.
        If even, we bump it up to the next odd (e.g., 4 -> 5).
        """
        if value < 1:
            return 1
        return value if value % 2 == 1 else value + 1

    def run_forever(self) -> None:
        """Main loop: play match after match until user quits."""
        self._print_welcome()

        while True:
            self.play_match()
            if not self._prompt_replay_or_change_settings():
                self._print_final_summary()
                return

    def play_match(self) -> None:
        """Play a best-of-N match."""
        target_wins = (self.best_of // 2) + 1
        player_score = 0
        computer_score = 0
        round_no = 1

        self.stats.match_played += 1
        self._print_match_header(target_wins)

        while player_score < target_wins and computer_score < target_wins:
            player_move = self._get_player_move(round_no=round_no)
            computer_move = self._get_computer_move()

            result = self._round_result(player_move, computer_move)
            self._display_round(player_move, computer_move, result)

            self.stats.rounds_played += 1
            self.stats.record_moves(player_move, computer_move)

            if result == "tie":
                self.stats.ties += 1
            elif result == "player":
                player_score += 1
                self.stats.player_round_wins += 1
            else:
                computer_score += 1
                self.stats.computer_round_wins += 1

            self._display_scoreboard(player_score, computer_score, target_wins)
            round_no += 1

        if player_score > computer_score:
            self.stats.player_match_wins += 1
            print("🏆 You won the match!\n")
        else:
            self.stats.computer_match_wins += 1
            print("🤖 Computer won the match!\n")

        self._print_stats_snapshot()

    def _round_result(self, player: Move, computer: Move) -> str:
        """Return 'tie', 'player', or 'computer'."""
        if player == computer:
            return "tie"
        if (player, computer) in self.WINNING_COMBINATIONS:
            return "player"
        return "computer"

    def _get_computer_move(self) -> Move:
        return self._rng.choice(tuple(self.SYMBOLS))

    def _get_player_move(self, round_no: int) -> Move:
        """Prompt until valid move is entered. 'q' quits immediately."""
        prompt = (
            f"Round {round_no} — choose rock (🪨), paper (📄), scissors (✂️), or 'q' to quit: "
        )
        while True:
            raw = input(prompt).strip().lower()
            if raw == "q":
                self._print_final_summary()
                raise SystemExit(0)

            if raw in self.SYMBOLS:
                return raw

            print("❌ Invalid choice. Please type: rock, paper, scissors, or q.\n")

    def _prompt_replay_or_change_settings(self) -> bool:
        """
        After a match:
        - Enter to play again with same best_of
        - 'b' to change best_of
        - 'q' to quit
        """
        while True:
            raw = input("Press Enter to play again, 'b' to change Best-of, or 'q' to quit: ").strip().lower()
            if raw == "":
                print()
                return True
            if raw == "q":
                return False
            if raw == "b":
                self._change_best_of()
                print()
                return True

            print("❌ Invalid input. Use Enter, b, or q.\n")

    def _change_best_of(self) -> None:
        while True:
            raw = input("New Best-of value (odd number like 3, 5, 7). 'c' to cancel: ").strip().lower()
            if raw == "c":
                return
            if raw.isdigit():
                value = int(raw)
                normalized = self._normalize_best_of(value)
                self.best_of = normalized
                if normalized != value:
                    print(f"ℹ️ Best-of adjusted to the next odd number: {normalized}")
                else:
                    print(f"✅ Best-of set to {normalized}")
                return

            print("❌ Please enter a number (e.g., 5) or 'c' to cancel.\n")

    def _print_welcome(self) -> None:
        print("🎮 Rock–Paper–Scissors 🎮")
        print("Type 'q' anytime during a round to quit.\n")

    def _print_match_header(self, target_wins: int) -> None:
        print("=" * 28)
        print(f"Match: Best-of-{self.best_of} (first to {target_wins} wins)")
        print("=" * 28)

    def _display_round(self, player: Move, computer: Move, result: str) -> None:
        print("\nResults")
        print("-" * 16)
        print(f"You:      {self.SYMBOLS[player]}  {player}")
        print(f"Computer: {self.SYMBOLS[computer]}  {computer}")
        print("-" * 16)

        if result == "tie":
            print("It's a tie! 🤝")
        elif result == "player":
            print(f"You win the round with {player}! 🎉")
        else:
            print("Computer wins the round! 🤖")
        print()

    @staticmethod
    def _display_scoreboard(player_score: int, computer_score: int, target_wins: int) -> None:
        print(f"Score: You {player_score} — {computer_score} Computer (target: {target_wins})\n")

    def _print_stats_snapshot(self) -> None:
        """Small stats panel after each match."""
        decided_rounds = self.stats.player_round_wins + self.stats.computer_round_wins
        win_rate = self.stats.player_round_win_rate() * 100.0

        print("📊 Stats so far")
        print("-" * 28)
        print(f"Matches: You {self.stats.player_match_wins} — {self.stats.computer_match_wins} Computer")
        print(
            f"Rounds:  You {self.stats.player_round_wins} — {self.stats.computer_round_wins} Computer, Ties {self.stats.ties}")
        print(f"Win rate (decided rounds): {win_rate:.1f}% ({decided_rounds} decided rounds)")
        print(f"Your moves:      {self._format_move_counts(self.stats.player_move_counts)}")
        print(f"Computer moves:  {self._format_move_counts(self.stats.computer_move_counts)}")
        print("-" * 28)
        print()

    def _print_final_summary(self) -> None:
        """Printed on quit."""
        print("\n👋 Final summary")
        print("=" * 28)
        self._print_stats_snapshot()

    def _format_move_counts(self, counts: Dict[Move, int]) -> str:
        # Keep consistent order for readability
        parts: List[str] = []
        for move in self.SYMBOLS:
            parts.append(f"{self.SYMBOLS[move]} {move}: {counts.get(move, 0)}")
        return " | ".join(parts)


def main() -> None:
    game = RockPaperScissorsGame(best_of=3)
    game.run_forever()


if __name__ == "__main__":
    main()
