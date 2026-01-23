class Car:
    def __init__(self, licence_plate: str) -> None:
        plate = licence_plate.strip().upper()
        if len(plate) != 6:
            raise ValueError("Invalid licence plate.")
        self.licence_plate = plate


class StolenCarRegistry:
    def __init__(self) -> None:
        self.stolen_plates: set[str] = set()

    def add_stolen_plates(self, plates: list[str]) -> None:
        for plate in plates:
            self.stolen_plates.add(plate.strip().upper())

    # Homework 1: remove stolen cars
    def remove_stolen_plate(self, plate: str) -> bool:
        """Remove plate if present. Returns True if removed, else False."""
        plate = plate.strip().upper()
        if plate in self.stolen_plates:
            self.stolen_plates.remove(plate)
            return True
        return False

    # Homework 2: count total stolen cars
    def count(self) -> int:
        return len(self.stolen_plates)

    # Homework 3: display all stolen plates
    def all_stolen_plates(self) -> list[str]:
        return sorted(self.stolen_plates)

    def is_stolen(self, plate: str) -> bool:
        return plate.strip().upper() in self.stolen_plates


def main() -> None:
    registry = StolenCarRegistry()
    registry.add_stolen_plates(["ABC123", "XYZ999", "BOB789"])

    print("Welcome to Car Theft Identifier")
    print('Commands: "check PLATE", "add PLATE", "remove PLATE", "count", "list", "quit"')

    while True:
        raw = input("> ").strip()
        if not raw:
            continue

        cmd, *rest = raw.split(maxsplit=1)
        cmd = cmd.lower()
        arg = rest[0] if rest else ""

        if cmd in {"quit", "exit"}:
            break

        if cmd == "count":
            print(f"Total stolen cars: {registry.count()}")
            continue

        if cmd == "list":
            plates = registry.all_stolen_plates()
            if not plates:
                print("(no stolen plates)")
            else:
                print("Stolen plates:")
                for p in plates:
                    print(f"- {p}")
            continue

        if cmd in {"check", "add", "remove"}:
            try:
                car = Car(arg)
            except ValueError as e:
                print(f"Error: {e}")
                continue

            if cmd == "check":
                if registry.is_stolen(car.licence_plate):
                    print(f'❌ Car with plate "{car.licence_plate}" is: REPORTED STOLEN!')
                else:
                    print(f'✅ Car with plate "{car.licence_plate}" is: OK')
            elif cmd == "add":
                registry.add_stolen_plates([car.licence_plate])
                print(f'Added "{car.licence_plate}". Total: {registry.count()}')
            else:  # remove
                removed = registry.remove_stolen_plate(car.licence_plate)
                if removed:
                    print(f'Removed "{car.licence_plate}". Total: {registry.count()}')
                else:
                    print(f'"{car.licence_plate}" was not in the registry. Total: {registry.count()}')
            continue

        print('Unknown command. Use: check/add/remove/count/list/quit')


if __name__ == "__main__":
    main()
