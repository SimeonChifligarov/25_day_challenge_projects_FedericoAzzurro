"""
Rule-based chatbot (single-file version).

Improvements implemented:
- Token/word matching to avoid false positives ("hi" won't match "this")
- Phrase priority (more specific / higher priority intents win)
- Punctuation stripping + whitespace normalization
- Intent system with priority + static replies OR callable actions
- Timezone-aware time/date/datetime + UTC time
- Clean exit commands (quit/exit) + Ctrl+C / EOF handling
- Session state (remembers user's name for this run)
- "Did you mean ..." suggestions (difflib) + fallback suggests "help"
- Logging support via env var CHATBOT_LOG_LEVEL
- Deterministic randomized replies via seed (CHATBOT_SEED)
- Small performance boost: keyword -> intent index
"""

from __future__ import annotations

import logging
import os
import random
import re
import string
from dataclasses import dataclass, field
from datetime import datetime, timezone
from difflib import get_close_matches
from typing import Callable, Final, Iterable, Mapping, Sequence

from zoneinfo import ZoneInfo

# ------------------------------------------------------------------------------
# Logging
# ------------------------------------------------------------------------------

logger = logging.getLogger(__name__)


def configure_logging() -> None:
    level_name = os.getenv("CHATBOT_LOG_LEVEL", "WARNING").upper()
    level = getattr(logging, level_name, logging.WARNING)
    logging.basicConfig(level=level, format="%(levelname)s:%(name)s:%(message)s")


# ------------------------------------------------------------------------------
# Types / data model
# ------------------------------------------------------------------------------

Action = Callable[["BotContext", str], str]


@dataclass(slots=True)
class BotContext:
    """Conversation/session state."""
    user_name: str | None = None
    tz_name: str = "Europe/Sofia"
    rng: random.Random = field(default_factory=lambda: random.Random(0))


@dataclass(frozen=True, slots=True)
class Intent:
    """
    A matching rule.

    Exactly one of `reply` or `action` must be set.
    - priority: higher wins
    - match:
        - "phrase": term tokens must appear contiguously (e.g., "my name is")
        - "any": any term token may match (e.g., "hi", "hello")
    """
    name: str
    terms: tuple[str, ...]
    priority: int
    match: str = "phrase"  # "phrase" | "any"
    reply: str | Sequence[str] | None = None
    action: Action | None = None

    def __post_init__(self) -> None:
        if (self.reply is None) == (self.action is None):
            raise ValueError("Intent must define exactly one of `reply` or `action`.")
        if self.match not in {"phrase", "any"}:
            raise ValueError("Intent.match must be 'phrase' or 'any'.")


# ------------------------------------------------------------------------------
# Normalization / matching helpers
# ------------------------------------------------------------------------------

_PUNCT_TABLE: Final[Mapping[int, int]] = str.maketrans({ch: ord(" ") for ch in string.punctuation})
_WS_RE: Final[re.Pattern[str]] = re.compile(r"\s+")


def normalize(text: str) -> str:
    """Lowercase, strip, map punctuation to spaces, collapse whitespace."""
    cleaned = text.strip().lower().translate(_PUNCT_TABLE)
    return _WS_RE.sub(" ", cleaned).strip()


def tokenize(text: str) -> list[str]:
    norm = normalize(text)
    return [] if not norm else norm.split(" ")


def contains_any_token(terms: Iterable[str], tokens: Sequence[str]) -> bool:
    token_set = set(tokens)
    return any(term in token_set for term in terms)


def contains_phrase(phrase_tokens: Sequence[str], tokens: Sequence[str]) -> bool:
    if not phrase_tokens or len(phrase_tokens) > len(tokens):
        return False
    n = len(phrase_tokens)
    target = list(phrase_tokens)
    return any(tokens[i: i + n] == target for i in range(0, len(tokens) - n + 1))


def intent_matches(intent: Intent, tokens: Sequence[str]) -> bool:
    if not tokens:
        return False

    if intent.match == "any":
        # Each term is treated as a single token in "any" mode.
        term_tokens = tuple(normalize(t) for t in intent.terms)
        return contains_any_token(term_tokens, tokens)

    # "phrase" mode: each term may be multiple tokens; any term match triggers the intent.
    for term in intent.terms:
        if contains_phrase(tokenize(term), tokens):
            return True
    return False


# ------------------------------------------------------------------------------
# Bot core
# ------------------------------------------------------------------------------

class ChatBot:
    def __init__(
            self,
            intents: Sequence[Intent],
            *,
            fallback: str = "Sorry... I can't answer that right now.",
            suggest_help: bool = True,
    ) -> None:
        self._intents = tuple(intents)
        self._fallback = fallback
        self._suggest_help = suggest_help

        # Performance: index intents by token -> likely intents
        self._index: dict[str, list[Intent]] = {}
        for intent in self._intents:
            for term in intent.terms:
                tks = tokenize(term)
                if not tks:
                    continue
                if intent.match == "any":
                    for tk in tks:
                        self._index.setdefault(tk, []).append(intent)
                else:
                    # index phrase intents by first token
                    self._index.setdefault(tks[0], []).append(intent)

        # For "did you mean"
        self._known_terms: set[str] = {normalize(t) for it in self._intents for t in it.terms}

    def reply(self, ctx: BotContext, user_text: str) -> str:
        tokens = tokenize(user_text)

        candidates = self._candidate_intents(tokens)
        matched = [it for it in candidates if intent_matches(it, tokens)]

        if not matched:
            return self._fallback_response(ctx, user_text)

        # Priority wins; tie-break by longest term (more specific)
        matched.sort(
            key=lambda it: (it.priority, max(len(tokenize(t)) for t in it.terms)),
            reverse=True,
        )
        chosen = matched[0]
        logger.debug("Matched intent=%s tokens=%s", chosen.name, tokens)

        if chosen.action is not None:
            return chosen.action(ctx, user_text)

        assert chosen.reply is not None
        if isinstance(chosen.reply, str):
            return chosen.reply

        # Randomize but deterministic via ctx.rng seed
        return ctx.rng.choice(list(chosen.reply))

    def _candidate_intents(self, tokens: Sequence[str]) -> list[Intent]:
        if not tokens:
            return list(self._intents)

        seen: set[Intent] = set()
        out: list[Intent] = []

        for tk in tokens:
            for it in self._index.get(tk, []):
                if it not in seen:
                    seen.add(it)
                    out.append(it)

        return out if out else list(self._intents)

    def _fallback_response(self, ctx: BotContext, user_text: str) -> str:
        base = self._fallback
        if not self._suggest_help:
            return base

        suggestion = self._did_you_mean(user_text)
        if suggestion:
            return f"{base} Did you mean: {suggestion}? Try 'help'."
        return f"{base} Try 'help'."

    def _did_you_mean(self, user_text: str) -> str | None:
        norm = normalize(user_text)
        if not norm:
            return None
        matches = get_close_matches(norm, self._known_terms, n=1, cutoff=0.75)
        return matches[0] if matches else None


# ------------------------------------------------------------------------------
# Intent actions
# ------------------------------------------------------------------------------

BOT_NAME: Final[str] = "PyBot"

HELP_TEXT: Final[str] = (
    "Commands: hello/hi, bye, quit/exit, time, utc time, date, datetime, "
    "my name is <name>, what is my name, joke, thanks, mood words (happy/sad/stressed)."
)


def action_time_local(ctx: BotContext, _: str) -> str:
    tz = ZoneInfo(ctx.tz_name)
    now = datetime.now(tz=tz)
    return f"The time is: {now.strftime('%H:%M:%S %Z')}"


def action_time_utc(_: BotContext, __: str) -> str:
    now = datetime.now(tz=timezone.utc)
    return f"UTC time is: {now.strftime('%H:%M:%S UTC')}"


def action_date_local(ctx: BotContext, _: str) -> str:
    tz = ZoneInfo(ctx.tz_name)
    today = datetime.now(tz=tz).date()
    return f"Today's date is: {today.isoformat()}"


def action_datetime_local(ctx: BotContext, _: str) -> str:
    tz = ZoneInfo(ctx.tz_name)
    now = datetime.now(tz=tz)
    return f"Local datetime is: {now.isoformat(timespec='seconds')}"


def action_set_name(ctx: BotContext, user_text: str) -> str:
    tokens = tokenize(user_text)
    phrase = ["my", "name", "is"]
    for i in range(0, len(tokens) - len(phrase) + 1):
        if tokens[i: i + 3] == phrase:
            name_tokens = tokens[i + 3:]
            if name_tokens:
                name = " ".join(t.capitalize() for t in name_tokens)
                ctx.user_name = name
                return f"Nice to meet you, {name}!"
    return "Tell me like: 'My name is Ada'."


def action_get_name(ctx: BotContext, _: str) -> str:
    return f"Your name is {ctx.user_name}." if ctx.user_name else "I don't know your name yet. Say: 'My name is ...'."


# ------------------------------------------------------------------------------
# Intents (custom responses / homework)
# ------------------------------------------------------------------------------

INTENTS: Final[tuple[Intent, ...]] = (
    # Help (highest)
    Intent(
        name="help",
        terms=("help", "commands", "what can you do"),
        priority=100,
        match="phrase",
        reply=HELP_TEXT,
    ),
    # Greeting / goodbye
    Intent(
        name="greeting",
        terms=("hello", "hi", "hey"),
        priority=80,
        match="any",
        reply=("Hello there!", "Hi!", "Hey!"),
    ),
    Intent(
        name="goodbye",
        terms=("goodbye", "bye", "see you"),
        priority=80,
        match="any",
        reply=("Talk to you later!", "Bye!", "See you soon!"),
    ),
    # Time/date/datetime (timezone-aware)
    Intent(
        name="time_utc",
        terms=("utc time", "time in utc"),
        priority=95,
        match="phrase",
        action=action_time_utc,
    ),
    Intent(
        name="time_local",
        terms=("what time is it", "current time", "time"),
        priority=90,
        match="phrase",
        action=action_time_local,
    ),
    Intent(
        name="date_local",
        terms=("what date is it", "today's date", "date"),
        priority=90,
        match="phrase",
        action=action_date_local,
    ),
    Intent(
        name="datetime_local",
        terms=("datetime", "date time", "current datetime"),
        priority=90,
        match="phrase",
        action=action_datetime_local,
    ),
    # Identity / name memory
    Intent(
        name="set_name",
        terms=("my name is",),
        priority=92,
        match="phrase",
        action=action_set_name,
    ),
    Intent(
        name="get_name",
        terms=("what is my name", "do you know my name"),
        priority=91,
        match="phrase",
        action=action_get_name,
    ),
    Intent(
        name="bot_name",
        terms=("your name", "who are you", "what are you"),
        priority=70,
        match="phrase",
        reply=f"My name is {BOT_NAME}.",
    ),
    # Fun / social
    Intent(
        name="thanks",
        terms=("thanks", "thank you", "thx"),
        priority=60,
        match="any",
        reply=("You're welcome!", "No problem!", "Anytime!"),
    ),
    Intent(
        name="joke",
        terms=("tell me a joke", "joke"),
        priority=60,
        match="phrase",
        reply=(
            "Why do programmers confuse Halloween and Christmas? Because OCT 31 == DEC 25.",
            "I would tell you a UDP joke, but you might not get it.",
        ),
    ),
    # Mood
    Intent(
        name="mood_positive",
        terms=("happy", "great", "awesome"),
        priority=50,
        match="any",
        reply=("Love that for you 😄", "Nice!", "That’s great to hear!"),
    ),
    Intent(
        name="mood_negative",
        terms=("sad", "down", "depressed"),
        priority=50,
        match="any",
        reply="I'm sorry you're feeling that way. Want to share what's going on?",
    ),
    Intent(
        name="mood_stress",
        terms=("stressed", "anxious", "overwhelmed"),
        priority=50,
        match="any",
        reply="That sounds heavy. Try 3 slow breaths: inhale 4, hold 2, exhale 6.",
    ),
)

# ------------------------------------------------------------------------------
# Main loop
# ------------------------------------------------------------------------------

WELCOME: Final[str] = "Bot: Hi! Type 'help' to see commands. Type 'quit' or 'exit' to exit."


def main() -> int:
    configure_logging()

    seed_str = os.getenv("CHATBOT_SEED", "0")
    try:
        seed = int(seed_str)
    except ValueError:
        seed = 0

    tz_name = os.getenv("CHATBOT_TZ", "Europe/Sofia")

    ctx = BotContext(tz_name=tz_name)
    ctx.rng.seed(seed)

    bot = ChatBot(INTENTS)

    print(WELCOME)

    while True:
        try:
            user_text = input("You: ")
        except (KeyboardInterrupt, EOFError):
            print("\nBot: Bye!")
            return 0

        if normalize(user_text) in {"quit", "exit"}:
            print("Bot: Bye!")
            return 0

        print(f"Bot: {bot.reply(ctx, user_text)}")

    # Unreachable
    # return 0


if __name__ == "__main__":
    raise SystemExit(main())
