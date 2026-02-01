from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
import random
import re
from typing import Any


@dataclass(frozen=True, slots=True)
class Response:
    response: str
    words: frozenset[str]
    required_words: frozenset[str]

    @classmethod
    def from_mapping(cls, data: dict[str, Any]) -> "Response":
        response = data.get("response")
        words = data.get("words")
        required = data.get("required_words", [])

        if not isinstance(response, str) or not response.strip():
            raise ValueError("Each item must include a non-empty string field: 'response'.")
        if not isinstance(words, list) or not all(isinstance(w, str) and w.strip() for w in words):
            raise ValueError("Each item must include a list of non-empty strings field: 'words'.")
        if not isinstance(required, list) or not all(isinstance(w, str) and w.strip() for w in required):
            raise ValueError("Field 'required_words' must be a list of non-empty strings.")

        return cls(
            response=response.strip(),
            words=frozenset(w.lower() for w in words),
            required_words=frozenset(w.lower() for w in required),
        )


class Chatbot:
    _token_re = re.compile(r"[a-z0-9']+", re.IGNORECASE)

    def __init__(
            self,
            responses_path: str | Path = "responses_homework.json",
            *,
            min_score: float = 0.20,
            near_best_delta: float = 0.05,
            top_n: int = 3,
            seed: int | None = None,
    ) -> None:
        self.responses_path = Path(responses_path)
        self.min_score = float(min_score)
        self.near_best_delta = float(near_best_delta)
        self.top_n = int(top_n)
        self.rng = random.Random(seed)

        # Always use responses_homework.json (no fallback)
        self.responses: list[Response] = self._load_responses_from_file(self.responses_path)

    @classmethod
    def tokenize(cls, text: str) -> set[str]:
        return {t.lower() for t in cls._token_re.findall(text)}

    def _load_responses_from_file(self, path: Path) -> list[Response]:
        if not path.exists():
            raise FileNotFoundError(f"Missing {path.name}. Create it next to this script.")

        try:
            raw = path.read_text(encoding="utf-8")
        except OSError as e:
            raise ValueError(f"Could not read {path!s}: {e}") from e

        try:
            data = json.loads(raw)
        except json.JSONDecodeError as e:
            raise ValueError(f"{path.name} is not valid JSON: {e.msg} (line {e.lineno})") from e

        if not isinstance(data, list):
            raise ValueError(f"{path.name} must contain a JSON list of responses.")

        responses: list[Response] = []
        for i, item in enumerate(data):
            if not isinstance(item, dict):
                raise ValueError(f"{path.name}[{i}] must be an object/dict.")
            responses.append(Response.from_mapping(item))

        if not responses:
            raise ValueError(f"{path.name} contains no responses.")

        return responses

    def score(self, text: str, response: Response) -> tuple[float, int]:
        user_words = self.tokenize(text)
        if not user_words or not response.words:
            return 0.0, 0

        # Required words check (token-based, not substring-based)
        if response.required_words and not response.required_words.issubset(user_words):
            return 0.0, 0

        overlap = len(user_words & response.words)
        union = len(user_words | response.words)
        jaccard = overlap / union if union else 0.0
        return jaccard, overlap

    def get_response(self, text: str) -> str:
        scored: list[tuple[float, int, int, int, str, Response]] = []

        for r in self.responses:
            s, overlap = self.score(text, r)
            # Include response text as a stable tiebreaker to avoid comparing Response objects
            scored.append((s, overlap, len(r.required_words), len(r.words), r.response, r))

        # FIX: sort using only comparable fields (no Response comparisons)
        scored.sort(key=lambda t: (t[0], t[1], t[2], t[3], t[4]), reverse=True)

        best_score = scored[0][0] if scored else 0.0
        if best_score < self.min_score:
            return "I don't understand... [0%]"

        # Pick among top-N near-best to reduce repetition
        pool = [
            item for item in scored
            if item[0] >= self.min_score and item[0] >= (best_score - self.near_best_delta)
        ]
        pool = pool[: max(1, self.top_n)]
        chosen = self.rng.choice(pool)

        chosen_score = chosen[0]
        chosen_response = chosen[-1]
        return f"{chosen_response.response} [{chosen_score:.0%}]"

    def run(self) -> None:
        while True:
            try:
                user_input = input("You: ").strip()
            except (EOFError, KeyboardInterrupt):
                print("\nBot: See you!")
                return

            if not user_input:
                continue

            cmd = user_input.lower()
            if cmd in {"exit", "quit"}:
                print("Bot: See you!")
                return

            if cmd == "reload":
                try:
                    self.responses = self._load_responses_from_file(self.responses_path)
                except (ValueError, FileNotFoundError) as e:
                    print(f"Bot: Reload failed: {e}")
                else:
                    print(f"Bot: Reloaded responses from {self.responses_path.name}.")
                continue

            print(f"Bot: {self.get_response(user_input)}")


def main() -> None:
    bot = Chatbot()
    bot.run()


if __name__ == "__main__":
    main()
