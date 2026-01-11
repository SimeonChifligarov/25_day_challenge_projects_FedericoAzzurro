"""
Miles ↔ Kilometers Converter

Features:
- Lets the user choose the direction (km→mi or mi→km)
- Reads values from input()
- Validates menu choice and numeric input
- Uses functions and constants (clean, reusable, testable)
- Displays formatted results using f-strings
"""

# Constants
MILES_TO_KILOMETERS = 1.60934
KILOMETERS_TO_MILES = 1 / MILES_TO_KILOMETERS


def read_float(prompt: str) -> float:
    """Read a floating-point number from the user with validation."""
    while True:
        raw = input(prompt).strip().replace(",", ".")
        try:
            return float(raw)
        except ValueError:
            print("Invalid number. Please enter a numeric value (e.g., 12 or 12.5).")


def read_choice(prompt: str, valid_choices: set[str]) -> str:
    """Read a menu choice from the user with validation."""
    while True:
        choice = input(prompt).strip().lower()
        if choice in valid_choices:
            return choice
        print(f"Invalid choice. Please enter one of: {', '.join(sorted(valid_choices))}")


def miles_to_kilometers(miles: float) -> float:
    """Convert miles to kilometers."""
    return miles * MILES_TO_KILOMETERS


def kilometers_to_miles(kilometers: float) -> float:
    """Convert kilometers to miles."""
    return kilometers * KILOMETERS_TO_MILES


def run_converter() -> None:
    """Run a menu-driven converter loop."""
    print("Miles ↔ Kilometers Converter")
    print("-" * 30)

    while True:
        print("\nChoose conversion:")
        print("1) Kilometers -> Miles")
        print("2) Miles -> Kilometers")
        print("q) Quit")

        choice = read_choice("Your choice (1/2/q): ", {"1", "2", "q"})

        if choice == "q":
            print("Goodbye!")
            break

        if choice == "1":
            kilometers = read_float("Enter kilometers: ")
            converted = kilometers_to_miles(kilometers)
            print(f"{kilometers:.2f} km -> {converted:.2f} miles")
        elif choice == "2":
            miles = read_float("Enter miles: ")
            converted = miles_to_kilometers(miles)
            print(f"{miles:.2f} miles -> {converted:.2f} km")


if __name__ == "__main__":
    run_converter()
