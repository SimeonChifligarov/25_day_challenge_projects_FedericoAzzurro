from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from time import sleep
from typing import Callable, Final, Optional


# -----------------------------
# Models
# -----------------------------
def _normalize_text(value: str) -> str:
    """Normalize user text input for consistent matching (case-insensitive)."""
    return value.strip().casefold()


def _display_text(value: str) -> str:
    """Pretty display for normalized text."""
    # Keep it simple: title-case words for display
    return value.strip().title()


@dataclass(frozen=True, slots=True)
class Car:
    """
    A car definition used as a stock key.

    Note: brand/color are stored normalized for matching.
    Use display_* properties for user-friendly output.
    """
    brand: str
    color: str
    model: int

    @classmethod
    def create(cls, brand: str, color: str, model: int) -> "Car":
        if not brand.strip():
            raise ValueError("brand must be non-empty")
        if not color.strip():
            raise ValueError("color must be non-empty")
        if model <= 0:
            raise ValueError("model must be a positive integer")
        return cls(_normalize_text(brand), _normalize_text(color), model)

    @property
    def display_brand(self) -> str:
        return _display_text(self.brand)

    @property
    def display_color(self) -> str:
        return _display_text(self.color)

    def drive(
            self,
            distance_km: int,
            speed_kmh: int,
            *,
            simulate: bool = True,
            delay_fn: Callable[[float], None] = sleep,
    ) -> None:
        """
        Simulate driving a given distance at a given speed.

        Improvements:
        - Validates inputs
        - Allows disabling sleep for tests via simulate=False
        - Allows injecting delay function for tests

        Args:
            distance_km: Distance in kilometers to drive (>= 0).
            speed_kmh: Speed in km/h (> 0).
            simulate: If True, waits between kilometers.
            delay_fn: Function used for delaying (defaults to time.sleep).
        """
        if distance_km < 0:
            raise ValueError("distance_km must be >= 0")
        if speed_kmh <= 0:
            raise ValueError("speed_kmh must be > 0")

        print(f"{self.display_brand} {self.model} [{self.display_color}] started journey...")
        for km in range(1, distance_km + 1):
            if simulate:
                delay_fn(60 / speed_kmh)
            print(f"KM: {km}")
        print(f"{self.display_brand} {self.model} [{self.display_color}] completed journey...")


@dataclass(slots=True)
class Bank:
    """Stores money from sales using Decimal to avoid float rounding issues."""
    balance: Decimal = Decimal("0.00")

    def deposit(self, amount: Decimal) -> None:
        if amount <= Decimal("0"):
            raise ValueError("Deposit amount must be > 0")
        self.balance += amount

    def __str__(self) -> str:
        return f"{self.balance:.2f}"


# -----------------------------
# Stock operations (pure logic)
# -----------------------------
Stock = Counter[Car]


@dataclass(frozen=True, slots=True)
class SaleResult:
    success: bool
    message: str
    total: Decimal = Decimal("0.00")


def add_cars(stock: Stock, car: Car, amount: int) -> None:
    if amount <= 0:
        raise ValueError("amount must be a positive integer")
    stock[car] += amount


def sell(stock: Stock, bank: Bank, car: Car, amount: int, price_per_car: Decimal) -> SaleResult:
    if amount <= 0:
        return SaleResult(False, "Amount must be a positive integer.")
    if price_per_car <= Decimal("0"):
        return SaleResult(False, "Price must be a positive number.")

    available = stock.get(car, 0)
    if available < amount:
        return SaleResult(
            False,
            f"Not enough stock. Requested: {amount}, Available: {available}.",
        )

    stock[car] -= amount
    if stock[car] <= 0:
        del stock[car]

    total = price_per_car * Decimal(amount)
    bank.deposit(total)
    return SaleResult(
        True,
        f"Sold {amount}x {car.display_brand} {car.model} [{car.display_color}] for {total:.2f}.",
        total=total,
    )


# -----------------------------
# CLI helpers (parsing + I/O)
# -----------------------------
def _ask_nonempty(prompt: str) -> Optional[str]:
    value = input(prompt).strip()
    if not value:
        print("Value must be non-empty.")
        return None
    return value


def _ask_int(prompt: str, *, min_value: int | None = None) -> Optional[int]:
    raw = input(prompt).strip()
    try:
        value = int(raw)
    except ValueError:
        print("Error, please enter a whole number (digits only).")
        return None

    if min_value is not None and value < min_value:
        print(f"Value must be >= {min_value}.")
        return None
    return value


def _ask_decimal(prompt: str, *, min_value: Decimal | None = None) -> Optional[Decimal]:
    raw = input(prompt).strip()
    try:
        value = Decimal(raw)
    except (InvalidOperation, ValueError):
        print("Error, please enter a valid number.")
        return None

    if min_value is not None and value < min_value:
        print(f"Value must be >= {min_value}.")
        return None
    return value


def prompt_for_car() -> Optional[Car]:
    brand = _ask_nonempty("Enter the brand: ")
    if brand is None:
        return None

    color = _ask_nonempty("Enter the color: ")
    if color is None:
        return None

    model = _ask_int("Enter the model number: ", min_value=1)
    if model is None:
        return None

    try:
        return Car.create(brand, color, model)
    except ValueError as exc:
        print(f"Error: {exc}")
        return None


def display_stock(stock: Stock) -> None:
    if not stock:
        print("No cars in stock.")
        return

    # Sorted output for consistent, readable display
    items = sorted(
        stock.items(),
        key=lambda item: (item[0].brand, item[0].model, item[0].color),
    )

    print("Current stock:")
    for car, count in items:
        print(f"- {car.display_brand} {car.model} [{car.display_color}]: {count} in stock")


def display_bank(bank: Bank) -> None:
    print(f"Bank balance: {bank} currency units")


def create_cars_cli(stock: Stock) -> None:
    car = prompt_for_car()
    if car is None:
        return

    amount = _ask_int("Enter the amount: ", min_value=1)
    if amount is None:
        return

    add_cars(stock, car, amount)
    print("Cars created!")


def sell_cars_cli(stock: Stock, bank: Bank) -> None:
    car = prompt_for_car()
    if car is None:
        return

    amount = _ask_int("Enter the amount to sell: ", min_value=1)
    if amount is None:
        return

    price = _ask_decimal("Enter the price per car: ", min_value=Decimal("0.01"))
    if price is None:
        return

    result = sell(stock, bank, car, amount, price)
    print(result.message)
    if result.success:
        display_bank(bank)


def show_help() -> None:
    print(
        "Commands:\n"
        "- create  : add cars to stock\n"
        "- sell    : sell cars (checks availability)\n"
        "- display : show current stock\n"
        "- bank    : show bank balance\n"
        "- drive   : demo drive simulation (no sleep)\n"
        "- help    : show this help\n"
        "- quit    : exit program\n"
    )


def drive_demo() -> None:
    car = prompt_for_car()
    if car is None:
        return
    distance = _ask_int("Enter distance (km): ", min_value=0)
    if distance is None:
        return
    speed = _ask_int("Enter speed (km/h): ", min_value=1)
    if speed is None:
        return

    # For UX and tests: demo without real sleeping
    car.drive(distance, speed, simulate=False)


# -----------------------------
# Main
# -----------------------------
WELCOME: Final[str] = (
    'Type "help" for commands. '
    'Available: create, sell, display, bank, drive, help, quit'
)


def main() -> None:
    # Using Counter stock (fast updates + clean selling)
    stock: Stock = Counter(
        {
            Car.create("Volvo", "Red", 200): 2,
            Car.create("Toyota", "Green", 321): 1,
        }
    )
    bank = Bank()

    commands: dict[str, Callable[[], None]] = {
        "create": lambda: create_cars_cli(stock),
        "sell": lambda: sell_cars_cli(stock, bank),
        "display": lambda: display_stock(stock),
        "bank": lambda: display_bank(bank),
        "help": show_help,
        "drive": drive_demo,
        "quit": lambda: (_ for _ in ()).throw(SystemExit(0)),
        "exit": lambda: (_ for _ in ()).throw(SystemExit(0)),
    }

    print(WELCOME)
    while True:
        cmd = input("You: ").strip().lower()
        action = commands.get(cmd)
        if action is None:
            print(f'Unknown command: "{cmd}". Type "help" to see commands.')
            continue

        try:
            action()
        except SystemExit:
            print("Goodbye!")
            return
        except Exception as exc:
            # Avoid crashing the whole loop on unexpected errors
            print(f"Unexpected error: {exc}")


if __name__ == "__main__":
    main()
