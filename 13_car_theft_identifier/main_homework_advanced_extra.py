from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Iterator
import re

_PLATE_PATTERN = re.compile(r"^[A-Z0-9]{6}$")


def normalize_plate(raw_plate: str) -> str:
    """
    Normalize and validate a licence plate.

    Rules:
      - exactly 6 characters
      - alphanumeric only
      - stored uppercased
    """
    plate: str = raw_plate.strip().upper()
    if not _PLATE_PATTERN.fullmatch(plate):
        raise ValueError("Invalid licence plate.")
    return plate


@dataclass(frozen=True, slots=True)
class Car:
    licence_plate: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "licence_plate", normalize_plate(self.licence_plate))


class StolenCarRegistry:
    def __init__(self, plates: Iterable[str] = ()) -> None:
        self._stolen_plates: set[str] = set()
        self.add_many(plates)

    def __len__(self) -> int:
        return len(self._stolen_plates)

    def __contains__(self, plate: object) -> bool:
        if not isinstance(plate, str):
            return False
        try:
            normalized: str = normalize_plate(plate)
        except ValueError:
            return False
        return normalized in self._stolen_plates

    def add(self, plate: str) -> None:
        self._stolen_plates.add(normalize_plate(plate))

    def add_many(self, plates: Iterable[str]) -> None:
        for plate in plates:
            self.add(plate)

    def remove(self, plate: str) -> bool:
        normalized: str = normalize_plate(plate)
        if normalized in self._stolen_plates:
            self._stolen_plates.remove(normalized)
            return True
        return False

    def list_plates(self) -> tuple[str, ...]:
        return tuple(sorted(self._stolen_plates))

    def is_stolen(self, plate: str) -> bool:
        normalized: str = normalize_plate(plate)
        return normalized in self._stolen_plates


def parse_command(raw: str) -> tuple[str, str | None]:
    parts: list[str] = raw.strip().split(maxsplit=1)
    if not parts:
        return "", None
    cmd: str = parts[0].lower()
    arg: str | None = parts[1] if len(parts) == 2 else None
    return cmd, arg


def print_help() -> None:
    print('Commands:')
    print('  add <PLATE>     - mark a plate as stolen')
    print('  remove <PLATE>  - remove a plate from stolen registry')
    print('  list            - show all stolen plates')
    print('  count           - show total stolen plates')
    print('  help            - show this help')
    print('  quit            - exit')
    print("")
    print("Or enter a plate directly to check it.")


def main() -> None:
    registry: StolenCarRegistry = StolenCarRegistry(["ABC123", "XYZ999", "BOB789"])

    print("Welcome to Car Theft Identifier")
    print_help()

    while True:
        try:
            raw: str = input("Enter car licence plate or command: ").strip()
        except KeyboardInterrupt:
            print("\nBye!")
            break

        if not raw:
            continue

        cmd, arg = parse_command(raw)

        match cmd:
            case "quit" | "exit":
                print("Bye!")
                break

            case "help":
                print_help()

            case "count":
                print(f"Total stolen cars: {len(registry)}")

            case "list":
                plates: tuple[str, ...] = registry.list_plates()
                if not plates:
                    print("No stolen plates in the registry.")
                else:
                    print("Stolen plates:")
                    for plate in plates:
                        print(f"- {plate}")

            case "add":
                if arg is None:
                    print('⚠️ Usage: add <PLATE>')
                    continue
                try:
                    registry.add(arg)
                except ValueError as exc:
                    print(f"⚠️ {exc}")
                    continue
                print(f'✅ Added "{normalize_plate(arg)}" to stolen registry.')

            case "remove":
                if arg is None:
                    print('⚠️ Usage: remove <PLATE>')
                    continue
                try:
                    removed: bool = registry.remove(arg)
                    normalized: str = normalize_plate(arg)
                except ValueError as exc:
                    print(f"⚠️ {exc}")
                    continue

                if removed:
                    print(f'✅ Removed "{normalized}" from stolen registry.')
                else:
                    print(f'ℹ️ Plate "{normalized}" was not in the stolen registry.')

            case _:
                # Not a known command -> treat as a plate to check
                try:
                    car: Car = Car(raw)
                except ValueError as exc:
                    print(f"⚠️ {exc}")
                    continue

                if car.licence_plate in registry:
                    print(f'❌ Car with plate "{car.licence_plate}" is: REPORTED STOLEN!')
                else:
                    print(f'✅ Car with plate "{car.licence_plate}" is: OK')


if __name__ == "__main__":
    main()
