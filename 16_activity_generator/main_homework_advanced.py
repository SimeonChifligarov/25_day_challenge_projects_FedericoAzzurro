import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

DATA_FILE = Path("activities_homework.json")
VALID_LOCATIONS = {"indoor", "outdoor"}


# 1. Model the data
@dataclass(frozen=True)
class Activity:
    name: str
    location: str  # "indoor" | "outdoor"
    cost: int
    people: int


# 2. Load the data
def load_data(path: Path = DATA_FILE) -> list[Activity]:
    try:
        raw_text = path.read_text(encoding="utf-8")
    except FileNotFoundError:
        print(f"Error: File not found: {path}")
        return []
    except OSError as exc:
        print(f"Error: Could not read {path}: {exc}")
        return []

    try:
        raw_data: Any = json.loads(raw_text)
    except json.JSONDecodeError as exc:
        print(f"Error: Invalid JSON in {path}: {exc}")
        return []

    if not isinstance(raw_data, list):
        print(f"Error: Expected a JSON list in {path}.")
        return []

    activities: list[Activity] = []
    for idx, item in enumerate(raw_data, 1):
        if not isinstance(item, dict):
            print(f"Warning: Skipping item #{idx} (not an object).")
            continue

        try:
            name = str(item["activity"]).strip()
            location = str(item["type"]).strip().lower()
            cost = int(item["cost"])
            people = int(item["people"])
        except (KeyError, TypeError, ValueError):
            print(f"Warning: Skipping item #{idx} (missing/invalid fields).")
            continue

        if not name:
            print(f"Warning: Skipping item #{idx} (empty activity name).")
            continue

        if location not in VALID_LOCATIONS:
            print(
                f"Warning: Skipping item #{idx} (invalid type '{location}', expected indoor/outdoor)."
            )
            continue

        if cost < 0 or people < 1:
            print(f"Warning: Skipping item #{idx} (cost must be >= 0 and people must be >= 1).")
            continue

        activities.append(Activity(name=name, location=location, cost=cost, people=people))

    return activities


def ask_int(prompt: str, *, min_value: int = 0) -> int | None:
    try:
        value = int(input(prompt))
    except ValueError:
        print("Error: Please only enter numerical values.")
        return None

    if value < min_value:
        print(f"Error: Value must be >= {min_value}.")
        return None

    return value


def ask_location() -> str | None:
    while True:
        value = input("Do you want indoor, outdoor, or any? (indoor/outdoor/any): ").strip().lower()
        if value in ("any", ""):
            return None
        if value in VALID_LOCATIONS:
            return value
        print("Please enter: indoor, outdoor, or any.")


def matches(activity: Activity, people: int, cost: int, location: str | None) -> bool:
    if activity.cost > cost:
        return False
    if activity.people > people:
        return False
    if location is not None and activity.location != location:
        return False
    return True


def print_activities(activities: list[Activity], *, people: int) -> None:
    for i, a in enumerate(activities, 1):
        total_cost = people * a.cost
        print(
            f"{i}: {a.name} ({a.location}) - {a.cost}$ per person "
            f"[total for {people}: {total_cost}$] (min {a.people} people)"
        )


# 3. Generate activities
def generate_activities(activities: list[Activity]) -> None:
    people = ask_int("How many people are you? ", min_value=1)
    if people is None:
        return

    cost = ask_int("How much are you willing to spend per person ($)? ", min_value=0)
    if cost is None:
        return

    location = ask_location()

    matched = [a for a in activities if matches(a, people, cost, location)]
    matched.sort(key=lambda a: (a.cost, a.people, a.name.lower()))

    if not matched:
        print("No activities matched your criteria...")
        return

    print_activities(matched, people=people)


# 4. Put it all together
def main() -> None:
    activities = load_data()
    if not activities:
        return
    generate_activities(activities)


if __name__ == "__main__":
    main()
