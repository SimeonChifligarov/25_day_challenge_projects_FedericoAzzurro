from __future__ import annotations

import argparse
import json
import logging
from dataclasses import asdict, dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Iterable

LOG = logging.getLogger(__name__)


# ----------------------------
# Domain model
# ----------------------------
class Location(str, Enum):
    INDOOR = "indoor"
    OUTDOOR = "outdoor"

    @classmethod
    def parse(cls, value: str) -> Location | None:
        v = value.strip().lower()
        if v in ("i", "in", "indoor"):
            return cls.INDOOR
        if v in ("o", "out", "outdoor"):
            return cls.OUTDOOR
        return None


@dataclass(frozen=True, slots=True)
class Activity:
    name: str
    location: Location
    category: str
    cost: int  # per person
    min_people: int
    max_people: int | None  # None = unlimited/unknown


@dataclass(frozen=True, slots=True)
class Match:
    activity: Activity
    group_size: int
    total_cost: int
    score: tuple[int, int, int, str]  # lower is better (sortable)


# ----------------------------
# Parsing & validation
# ----------------------------
def _as_str(value: Any) -> str:
    return str(value).strip()


def _as_int(value: Any) -> int:
    # Accept "10", 10, "10.0" (reject non-integer floats)
    if isinstance(value, bool):
        raise ValueError("bool is not int")
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        if value.is_integer():
            return int(value)
        raise ValueError("float must be integral")
    s = _as_str(value)
    return int(s)


def _get_first(d: dict[str, Any], keys: Iterable[str]) -> Any:
    for k in keys:
        if k in d:
            return d[k]
    raise KeyError(f"missing keys: {', '.join(keys)}")


def _parse_location(record: dict[str, Any]) -> Location:
    # Prefer explicit "location"; support legacy "type" if it looks like indoor/outdoor.
    if "location" in record:
        loc = Location.parse(_as_str(record["location"]))
        if loc is None:
            raise ValueError(f"invalid location '{record['location']}'")
        return loc

    if "type" in record:
        maybe = Location.parse(_as_str(record["type"]))
        if maybe is not None:
            return maybe

    raise KeyError("missing 'location' (or legacy 'type' as indoor/outdoor)")


def _parse_category(record: dict[str, Any]) -> str:
    # Prefer explicit "category"; support legacy "type" if it's NOT indoor/outdoor.
    if "category" in record:
        cat = _as_str(record["category"]).lower()
        if not cat:
            raise ValueError("empty category")
        return cat

    if "type" in record:
        raw = _as_str(record["type"])
        if Location.parse(raw) is None:
            cat = raw.lower()
            if cat:
                return cat

    # Default category if not provided (keeps things usable)
    return "general"


def parse_activity_record(record: Any, *, index: int) -> Activity:
    if not isinstance(record, dict):
        raise TypeError("record is not an object")

    name = _as_str(_get_first(record, ("activity", "name", "title")))
    if not name:
        raise ValueError("empty activity name")

    location = _parse_location(record)
    category = _parse_category(record)

    cost = _as_int(_get_first(record, ("cost",)))
    if cost < 0:
        raise ValueError("cost must be >= 0")

    # People semantics:
    # - Prefer min_people/max_people
    # - Support legacy "people" as min_people
    if "min_people" in record:
        min_people = _as_int(record["min_people"])
    elif "people" in record:
        min_people = _as_int(record["people"])
    else:
        min_people = 1

    if min_people < 1:
        raise ValueError("min_people must be >= 1")

    max_people: int | None
    if "max_people" in record and record["max_people"] is not None:
        max_people = _as_int(record["max_people"])
        if max_people < min_people:
            raise ValueError("max_people must be >= min_people")
    else:
        # If legacy "people" existed AND you want it to mean "max", set it here.
        # This implementation treats legacy "people" as minimum (more common for activities).
        max_people = None

    return Activity(
        name=name,
        location=location,
        category=category,
        cost=cost,
        min_people=min_people,
        max_people=max_people,
    )


def load_activities(path: Path, *, strict: bool) -> list[Activity]:
    try:
        raw_text = path.read_text(encoding="utf-8")
    except FileNotFoundError:
        raise SystemExit(f"Error: File not found: {path}")
    except OSError as exc:
        raise SystemExit(f"Error: Could not read {path}: {exc}")

    try:
        raw = json.loads(raw_text)
    except json.JSONDecodeError as exc:
        raise SystemExit(f"Error: Invalid JSON in {path}: {exc}")

    if not isinstance(raw, list):
        raise SystemExit(f"Error: Expected a JSON list in {path}")

    activities: list[Activity] = []
    skipped = 0

    for idx, item in enumerate(raw, 1):
        try:
            activities.append(parse_activity_record(item, index=idx))
        except Exception as exc:
            skipped += 1
            msg = f"Skipping item #{idx}: {exc}"
            if strict:
                raise SystemExit(f"Error (strict): {msg}")
            LOG.warning(msg)

    LOG.info("Loaded %d activities (%d skipped).", len(activities), skipped)
    return activities


# ----------------------------
# Core logic (pure functions)
# ----------------------------
def matches_filters(
        a: Activity,
        *,
        group_size: int,
        max_cost: int,
        location: Location | None,
        categories: set[str] | None,
) -> bool:
    if a.cost > max_cost:
        return False
    if group_size < a.min_people:
        return False
    if a.max_people is not None and group_size > a.max_people:
        return False
    if location is not None and a.location != location:
        return False
    if categories is not None and a.category not in categories:
        return False
    return True


def score_activity(a: Activity, *, group_size: int, max_cost: int) -> tuple[int, int, int, str]:
    # Lower is better.
    # 1) cheaper
    # 2) tighter fit: prefer min_people close to group size (but not above, already filtered)
    # 3) less "wasted capacity" if max_people exists (prefer closer max to group size)
    # 4) stable tie-breaker by name
    price = a.cost
    min_fit = abs(group_size - a.min_people)

    if a.max_people is None:
        max_waste = 999_999
    else:
        max_waste = a.max_people - group_size

    return (price, min_fit, max_waste, a.name.casefold())


def find_matches(
        activities: list[Activity],
        *,
        group_size: int,
        max_cost: int,
        location: Location | None,
        categories: set[str] | None,
        limit: int,
) -> list[Match]:
    matched: list[Match] = []
    for a in activities:
        if not matches_filters(
                a,
                group_size=group_size,
                max_cost=max_cost,
                location=location,
                categories=categories,
        ):
            continue

        total_cost = group_size * a.cost
        score = score_activity(a, group_size=group_size, max_cost=max_cost)
        matched.append(Match(activity=a, group_size=group_size, total_cost=total_cost, score=score))

    matched.sort(key=lambda m: m.score)
    return matched[:limit]


# ----------------------------
# I/O helpers (interactive fallback)
# ----------------------------
def ask_int(prompt: str, *, min_value: int) -> int:
    while True:
        raw = input(prompt).strip()
        if raw in ("?", "help"):
            print(f"Enter a number (>= {min_value}).")
            continue
        try:
            value = int(raw)
        except ValueError:
            print("Please enter a whole number.")
            continue
        if value < min_value:
            print(f"Value must be >= {min_value}.")
            continue
        return value


def ask_location() -> Location | None:
    while True:
        raw = input("Location? (indoor/outdoor/any): ").strip().lower()
        if raw in ("", "any", "a"):
            return None
        if raw in ("?", "help"):
            print("Choose indoor, outdoor, or any.")
            continue
        loc = Location.parse(raw)
        if loc is not None:
            return loc
        print("Please enter: indoor, outdoor, or any.")


def ask_categories() -> set[str] | None:
    raw = input("Categories? (comma-separated, empty for any): ").strip()
    if raw in ("", "any"):
        return None
    if raw in ("?", "help"):
        print("Example: adventure, entertainment, food")
        return ask_categories()
    cats = {c.strip().lower() for c in raw.split(",") if c.strip()}
    return cats or None


# ----------------------------
# Output formats
# ----------------------------
def print_text(matches: list[Match]) -> None:
    if not matches:
        print("No activities matched your criteria...")
        return

    for i, m in enumerate(matches, 1):
        a = m.activity
        people_range = (
            f"{a.min_people}+"
            if a.max_people is None
            else f"{a.min_people}-{a.max_people}"
        )
        print(
            f"{i}: {a.name} ({a.location.value}, {a.category}) - "
            f"{a.cost}$ per person [total for {m.group_size}: {m.total_cost}$] "
            f"(people: {people_range})"
        )


def print_json(matches: list[Match]) -> None:
    out: list[dict[str, Any]] = []
    for m in matches:
        a = m.activity
        out.append(
            {
                **asdict(a),
                "location": a.location.value,
                "group_size": m.group_size,
                "total_cost": m.total_cost,
            }
        )
    print(json.dumps(out, indent=2, ensure_ascii=False))


# ----------------------------
# CLI
# ----------------------------
def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="activity_picker",
        description="Filter and rank activities by budget, group size, and location.",
    )
    p.add_argument("--data", type=Path, default=Path("activities.json"), help="Path to activities JSON file")
    p.add_argument("--people", type=int, help="Group size")
    p.add_argument("--max-cost", type=int, dest="max_cost", help="Max cost per person")
    p.add_argument("--location", choices=[e.value for e in Location], help="Filter by location")
    p.add_argument(
        "--category",
        action="append",
        help="Filter by category (repeatable). Example: --category adventure --category food",
    )
    p.add_argument("--limit", type=int, default=10, help="Max number of results to show")
    p.add_argument("--format", choices=["text", "json"], default="text", help="Output format")
    p.add_argument("--strict", action="store_true", help="Fail on any invalid record in the JSON")
    p.add_argument("--verbose", action="store_true", help="Show warnings and info logs")
    p.add_argument(
        "--no-interactive",
        action="store_true",
        help="Do not prompt; require needed inputs via flags",
    )
    return p


def configure_logging(*, verbose: bool) -> None:
    level = logging.INFO if verbose else logging.ERROR
    logging.basicConfig(level=level, format="%(levelname)s: %(message)s")


def main() -> None:
    args = build_parser().parse_args()
    configure_logging(verbose=args.verbose)

    activities = load_activities(args.data, strict=args.strict)

    # Normalize / validate CLI inputs
    if args.limit < 1:
        raise SystemExit("Error: --limit must be >= 1")

    people = args.people
    max_cost = args.max_cost

    if args.no_interactive:
        if people is None or max_cost is None:
            raise SystemExit("Error: --people and --max-cost are required with --no-interactive")
    else:
        if people is None:
            people = ask_int("How many people are you? ", min_value=1)
        if max_cost is None:
            max_cost = ask_int("How much are you willing to spend per person ($)? ", min_value=0)

    assert people is not None and max_cost is not None

    location = Location.parse(args.location) if args.location else None

    categories: set[str] | None
    if args.category:
        categories = {c.strip().lower() for c in args.category if c.strip()}
        categories = categories or None
    else:
        categories = None
        if not args.no_interactive:
            # Optional interactive category filter (advanced UX)
            categories = ask_categories()

    if not args.no_interactive and location is None:
        # Optional interactive location filter if not provided
        location = ask_location()

    matches = find_matches(
        activities,
        group_size=people,
        max_cost=max_cost,
        location=location,
        categories=categories,
        limit=args.limit,
    )

    if args.format == "json":
        print_json(matches)
    else:
        print_text(matches)


if __name__ == "__main__":
    main()
