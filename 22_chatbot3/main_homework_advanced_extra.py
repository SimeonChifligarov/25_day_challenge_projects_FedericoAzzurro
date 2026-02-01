from __future__ import annotations

import argparse
from dataclasses import dataclass
import json
import logging
from pathlib import Path
import random
import re
from functools import lru_cache
from typing import Any, Callable, Iterable, Mapping, TypedDict
import heapq

logger = logging.getLogger(__name__)


# ---------- JSON schema typing (runtime validated) ----------

class ResponseSpec(TypedDict):
    response: str
    words: list[str]
    required_words: list[str]


def _as_str_list(value: Any, *, field: str) -> list[str]:
    if not isinstance(value, list) or not all(isinstance(x, str) and x.strip() for x in value):
        raise ValueError(f"Field '{field}' must be a list of non-empty strings.")
    return [x.strip() for x in value]


# ---------- Domain model ----------

@dataclass(frozen=True, slots=True)
class Response:
    text: str
    words: frozenset[str]
    required_words: frozenset[str]

    @classmethod
    def from_mapping(cls, data: Mapping[str, Any]) -> "Response":
        raw_text = data.get("response")
        if not isinstance(raw_text, str) or not raw_text.strip():
            raise ValueError("Each item must include a non-empty string field: 'response'.")

        words = _as_str_list(data.get("words"), field="words")
        required = _as_str_list(data.get("required_words", []), field="required_words")

        return cls(
            text=raw_text.strip(),
            words=frozenset(w.lower() for w in words),
            required_words=frozenset(w.lower() for w in required),
        )


@dataclass(frozen=True, slots=True)
class Candidate:
    score: float
    overlap: int
    required_count: int
    words_count: int
    stable_tiebreaker: str
    response: Response

    def sort_key(self) -> tuple[float, int, int, int, str]:
        # Everything here is comparable => no accidental Response comparisons.
        return (self.score, self.overlap, self.required_count, self.words_count, self.stable_tiebreaker)


# ---------- Storage (responses_homework.json) ----------

class JsonResponseStore:
    """Loads responses_homework.json and supports manual reload (and optional auto-reload)."""

    def __init__(self, path: Path) -> None:
        self._path = path
        self._mtime_ns: int | None = None

    @property
    def path(self) -> Path:
        return self._path

    def load(self) -> list[Response]:
        if not self._path.exists():
            raise FileNotFoundError(f"Missing {self._path.name}. Create it next to this script.")

        raw: str
        try:
            raw = self._path.read_text(encoding="utf-8")
        except OSError as e:
            raise ValueError(f"Could not read {self._path!s}: {e}") from e

        try:
            data = json.loads(raw)
        except json.JSONDecodeError as e:
            raise ValueError(f"{self._path.name} is not valid JSON: {e.msg} (line {e.lineno})") from e

        if not isinstance(data, list):
            raise ValueError(f"{self._path.name} must contain a JSON list of responses.")

        responses: list[Response] = []
        for i, item in enumerate(data):
            if not isinstance(item, Mapping):
                raise ValueError(f"{self._path.name}[{i}] must be an object/dict.")
            responses.append(Response.from_mapping(item))

        if not responses:
            raise ValueError(f"{self._path.name} contains no responses.")

        try:
            self._mtime_ns = self._path.stat().st_mtime_ns
        except OSError:
            self._mtime_ns = None

        return responses

    def changed_on_disk(self) -> bool:
        if self._mtime_ns is None:
            return True
        try:
            return self._path.stat().st_mtime_ns != self._mtime_ns
        except OSError:
            return False


# ---------- Tokenization (cached) ----------

_TOKEN_RE = re.compile(r"[a-z0-9']+", re.IGNORECASE)


@lru_cache(maxsize=2048)
def tokenize_cached(text: str) -> frozenset[str]:
    # Cache is safe because it depends only on input text.
    return frozenset(t.lower() for t in _TOKEN_RE.findall(text))


# ---------- Chatbot ----------

class Chatbot:
    def __init__(
            self,
            store: JsonResponseStore,
            *,
            min_score: float = 0.20,
            near_best_delta: float = 0.05,
            top_n: int = 3,
            seed: int | None = None,
            auto_reload: bool = False,
    ) -> None:
        self._store = store
        self._min_score = float(min_score)
        self._near_best_delta = float(near_best_delta)
        self._top_n = max(1, int(top_n))
        self._rng = random.Random(seed)
        self._auto_reload = bool(auto_reload)

        self._responses: list[Response] = self._store.load()

        self._commands: dict[str, Callable[[], bool]] = {
            "reload": self._cmd_reload,
            "help": self._cmd_help,
            "exit": self._cmd_exit,
            "quit": self._cmd_exit,
        }

    # ---- commands ----

    def _cmd_help(self) -> bool:
        print("Bot: Commands: help, reload, exit, quit")
        return True

    def _cmd_reload(self) -> bool:
        self._responses = self._store.load()
        tokenize_cached.cache_clear()
        print(f"Bot: Reloaded responses from {self._store.path.name}.")
        return True

    def _cmd_exit(self) -> bool:
        print("Bot: See you!")
        return False

    # ---- core logic ----

    def _score(self, user_words: frozenset[str], resp: Response) -> tuple[float, int]:
        if not user_words or not resp.words:
            return 0.0, 0

        # Required words check (token-based, not substring-based)
        if resp.required_words and not resp.required_words.issubset(user_words):
            return 0.0, 0

        overlap = len(user_words & resp.words)
        union = len(user_words | resp.words)
        jaccard = overlap / union if union else 0.0
        return jaccard, overlap

    def _candidates(self, text: str) -> Iterable[Candidate]:
        user_words = tokenize_cached(text)
        for r in self._responses:
            score, overlap = self._score(user_words, r)
            yield Candidate(
                score=score,
                overlap=overlap,
                required_count=len(r.required_words),
                words_count=len(r.words),
                stable_tiebreaker=r.text,  # stable, comparable
                response=r,
            )

    def respond(self, text: str) -> str:
        if self._auto_reload and self._store.changed_on_disk():
            try:
                self._responses = self._store.load()
                tokenize_cached.cache_clear()
                logger.info("Auto-reloaded responses_homework.json due to file change.")
            except Exception as e:  # keep chatting even if reload fails
                logger.warning("Auto-reload failed: %s", e)

        # More advanced selection: grab top K via heapq (no full sort required).
        top_k = heapq.nlargest(self._top_n, self._candidates(text), key=lambda c: c.sort_key())
        if not top_k:
            return "I don't understand... [0%]"

        best = top_k[0]
        if best.score < self._min_score:
            return "I don't understand... [0%]"

        # Keep a near-best pool to reduce repetition.
        threshold = max(self._min_score, best.score - self._near_best_delta)
        pool = [c for c in top_k if c.score >= threshold] or [best]
        chosen = self._rng.choice(pool)

        return f"{chosen.response.text} [{chosen.score:.0%}]"

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
            handler = self._commands.get(cmd)
            if handler is not None:
                if not handler():
                    return
                continue

            print(f"Bot: {self.respond(user_input)}")


# ---------- CLI ----------

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Keyword-matching chatbot using responses_homework.json")
    parser.add_argument("--responses", default="responses_homework.json", help="Path to responses_homework.json")
    parser.add_argument("--min-score", type=float, default=0.20, help="Minimum score to accept a reply")
    parser.add_argument("--near-best-delta", type=float, default=0.05,
                        help="Pool includes scores within this delta of best")
    parser.add_argument("--top-n", type=int, default=3,
                        help="Consider only top-N candidates (then choose among near-best)")
    parser.add_argument("--seed", type=int, default=None, help="Random seed for deterministic choices")
    parser.add_argument("--auto-reload", action="store_true", help="Auto-reload responses_homework.json when it changes")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    logging.basicConfig(level=logging.DEBUG if args.debug else logging.INFO, format="%(levelname)s: %(message)s")

    store = JsonResponseStore(Path(args.responses))
    bot = Chatbot(
        store,
        min_score=args.min_score,
        near_best_delta=args.near_best_delta,
        top_n=args.top_n,
        seed=args.seed,
        auto_reload=args.auto_reload,
    )
    bot.run()


if __name__ == "__main__":
    main()
