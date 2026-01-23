from __future__ import annotations


# 1. Create the concept of a car in this world
class Car:
    def __init__(self, licence_plate: str) -> None:
        plate: str = licence_plate.strip().upper()
        if len(plate) != 6:
            raise ValueError("Invalid licence plate.")

        self.licence_plate: str = plate


# 2. Create a place to store stolen cars
class StolenCarRegistry:
    def __init__(self) -> None:
        # Example: Set of license plates that are stolen
        self.stolen_plates: set[str] = set()

    def add_stolen_plates(self, plates: list[str]) -> None:
        for plate in plates:
            normalized: str = plate.strip().upper()
            if len(normalized) != 6:
                raise ValueError(f'Invalid licence plate: "{plate}".')
            self.stolen_plates.add(normalized)

    def add_stolen_plate(self, plate: str) -> None:
        """Add a single stolen plate to the registry."""
        self.add_stolen_plates([plate])

    def remove_stolen_plate(self, plate: str) -> bool:
        """
        Remove a stolen plate from the registry.

        Returns:
            True if the plate existed and was removed, otherwise False.
        """
        normalized: str = plate.strip().upper()
        if len(normalized) != 6:
            raise ValueError("Invalid licence plate.")
        if normalized not in self.stolen_plates:
            return False

        self.stolen_plates.remove(normalized)
        return True

    def count(self) -> int:
        """Return the total number of stolen plates in the registry."""
        return len(self.stolen_plates)

    def all_stolen_plates(self) -> list[str]:
        """Return a sorted list of all stolen plates."""
        return sorted(self.stolen_plates)

    def is_stolen(self, plate: str) -> bool:
        normalized: str = plate.strip().upper()
        if len(normalized) != 6:
            raise ValueError("Invalid licence plate.")
        return normalized in self.stolen_plates


# 3. Check for stolen cars
def main() -> None:
    registry: StolenCarRegistry = StolenCarRegistry()
    # Populate with some stolen plates
    registry.add_stolen_plates(["ABC123", "XYZ999", "BOB789"])

    print("Welcome to Car Theft Identifier")
    print('Commands: "add <PLATE>", "remove <PLATE>", "list", "count", "quit"')

    while True:
        raw: str = input("Enter car licence plate or command: ").strip()
        if not raw:
            continue

        command: str = raw.lower()

        if command in {"quit", "exit"}:
            print("Bye!")
            break

        if command == "count":
            print(f"Total stolen cars: {registry.count()}")
            continue

        if command == "list":
            plates: list[str] = registry.all_stolen_plates()
            if not plates:
                print("No stolen plates in the registry.")
            else:
                print("Stolen plates:")
                for p in plates:
                    print(f"- {p}")
            continue

        if command.startswith("add "):
            plate_to_add: str = raw.split(maxsplit=1)[1]
            try:
                registry.add_stolen_plate(plate_to_add)
            except ValueError as exc:
                print(f"⚠️ {exc}")
                continue

            print(f'✅ Added "{plate_to_add.strip().upper()}" to stolen registry.')
            continue

        if command.startswith("remove "):
            plate_to_remove: str = raw.split(maxsplit=1)[1]
            try:
                removed: bool = registry.remove_stolen_plate(plate_to_remove)
            except ValueError as exc:
                print(f"⚠️ {exc}")
                continue

            if removed:
                print(f'✅ Removed "{plate_to_remove.strip().upper()}" from stolen registry.')
            else:
                print(f'ℹ️ Plate "{plate_to_remove.strip().upper()}" was not in the stolen registry.')
            continue

        # Otherwise, treat input as a licence plate to check
        try:
            car: Car = Car(raw)
        except ValueError as exc:
            print(f"⚠️ {exc}")
            continue

        if registry.is_stolen(car.licence_plate):
            print(f'❌ Car with plate "{car.licence_plate}" is: REPORTED STOLEN!')
        else:
            print(f'✅ Car with plate "{car.licence_plate}" is: OK')


if __name__ == "__main__":
    main()
