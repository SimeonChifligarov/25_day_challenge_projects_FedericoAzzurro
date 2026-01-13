from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Callable, Iterable, Optional


# ----------------------------
# 1) Input validation helpers
# ----------------------------

def _default_validator(value: str) -> bool:
    return bool(value.strip())


def _make_choices_validator(choices: Iterable[str]) -> Callable[[str], bool]:
    normalized = {c.strip().lower() for c in choices}

    def validator(value: str) -> bool:
        return value.strip().lower() in normalized

    return validator


def get_validated_input(
        prompt: str,
        *,
        validator: Callable[[str], bool] = _default_validator,
        error_message: str = "Invalid input. Please try again.",
        normalizer: Callable[[str], str] = str.strip,
) -> str:
    """
    Re-prompts until the user enters a valid value.

    Args:
        prompt: Text shown to the user.
        validator: Function that returns True if input is acceptable.
        error_message: Message shown on invalid input.
        normalizer: Function to normalize the accepted input (e.g., strip, lower).

    Returns:
        A validated, normalized string.
    """
    while True:
        value = input(prompt)
        if validator(value):
            return normalizer(value)
        print(error_message)


# ----------------------------
# 2) Class-based implementation
# ----------------------------

@dataclass(frozen=True)
class StoryInputs:
    name: str
    adjective: str
    place: str
    animal: str
    emotion: str
    verb: str
    object_name: str


class StoryGenerator:
    """
    Generates interactive stories in either:
      - "manual" mode: prompts user for all fields
      - "random" mode: asks user which fields to randomize
    """

    def __init__(
            self,
            *,
            templates: Optional[list[str]] = None,
            random_pools: Optional[dict[str, list[str]]] = None,
            rng: Optional[random.Random] = None,
    ) -> None:
        self._rng = rng or random.Random()

        self._templates = templates or [
            (
                "{name}'s Unexpected Journey\n\n"
                "One sunny morning, {name} walked into a {adjective} {place}.\n"
                "Suddenly, a wild {animal} appeared out of nowhere!\n"
                "Feeling very {emotion}, {name} decided to {verb} using a {object_name}.\n"
                "To everyone's surprise, the {animal} became friendly and followed {name} home.\n"
                "It turned out to be a day {name} would never forget.\n"
            ),
            (
                "The Mystery of the {place}\n\n"
                "{name} arrived at the {adjective} {place} right before sunset.\n"
                "Out from the shadows crept a {animal} with a strange look in its eyes.\n"
                "{name} felt {emotion} but chose to {verb} anyway, clutching a {object_name}.\n"
                "Moments later, the whole place started to glow, and the {animal} bowed politely.\n"
                "Whatever that was… it was definitely not a normal evening.\n"
            ),
            (
                "{name} vs. The Unexpected {animal}\n\n"
                "At the {place}, {name} spotted a {adjective} {animal} blocking the path.\n"
                "The air felt {emotion}, like something big was about to happen.\n"
                "So {name} took a deep breath and began to {verb} with a {object_name}.\n"
                "The {animal} blinked, then laughed—apparently that was the correct secret greeting!\n"
            ),
        ]

        self._random_pools = random_pools or {
            "name": ["Bob", "Maya", "Alex", "Rina", "Noah", "Zara"],
            "adjective": ["mysterious", "sparkly", "ancient", "stormy", "tiny", "gigantic"],
            "place": ["forest", "library", "castle", "market", "spaceport", "museum"],
            "animal": ["penguin", "fox", "tiger", "owl", "lizard", "koala"],
            "emotion": ["excited", "nervous", "curious", "brave", "confused", "delighted"],
            "verb": ["dance", "whisper", "sprint", "investigate", "juggle", "sing"],
            "object_name": ["flashlight", "map", "umbrella", "compass", "backpack", "notebook"],
        }

    # ----------------------------
    # 3) Random story generation
    # ----------------------------

    def generate(self, inputs: StoryInputs) -> str:
        template = self._rng.choice(self._templates)
        return template.format(**inputs.__dict__)

    def _random_value(self, key: str) -> str:
        pool = self._random_pools.get(key, [])
        if not pool:
            raise ValueError(f"No random pool defined for key: {key}")
        return self._rng.choice(pool)

    def prompt_inputs(self) -> StoryInputs:
        """
        Ask the user whether they want manual/random for each field,
        then collect values accordingly.
        """
        print("Choose input mode:")
        mode = get_validated_input(
            "Type 'manual' or 'random': ",
            validator=_make_choices_validator(["manual", "random"]),
            error_message="Please type 'manual' or 'random'.",
            normalizer=lambda s: s.strip().lower(),
        )

        # In random mode, allow customizing which fields to randomize.
        randomize_fields: set[str] = set()
        if mode == "random":
            print("\nRandom mode: choose which fields should be randomized.")
            print("Type 'y' to randomize a field, otherwise you'll enter it manually.\n")

            for key in self._random_pools.keys():
                answer = get_validated_input(
                    f"Randomize {key}? (y/n): ",
                    validator=_make_choices_validator(["y", "n"]),
                    error_message="Please type 'y' or 'n'.",
                    normalizer=lambda s: s.strip().lower(),
                )
                if answer == "y":
                    randomize_fields.add(key)

        def value_for(key: str, prompt: str) -> str:
            if key in randomize_fields:
                return self._random_value(key)
            return get_validated_input(prompt)

        inputs = StoryInputs(
            name=value_for("name", "Enter a name: "),
            adjective=value_for("adjective", "Enter an adjective: "),
            place=value_for("place", "Enter a place: "),
            animal=value_for("animal", "Enter an animal: "),
            emotion=value_for("emotion", "Enter an emotion: "),
            verb=value_for("verb", "Enter a verb: "),
            object_name=value_for("object_name", "Enter an object: "),
        )
        return inputs


def main() -> None:
    print("Welcome to the Interactive Story Generator!\n")

    generator = StoryGenerator()
    inputs = generator.prompt_inputs()

    story = generator.generate(inputs)

    print("\nResult:\n")
    print(story)


if __name__ == "__main__":
    main()
