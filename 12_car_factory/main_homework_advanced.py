from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from time import sleep


# 1. Create a car blueprint
@dataclass(frozen=True, slots=True)
class Car:
    brand: str
    color: str
    model: int

    def drive(self, distance_km: int, speed_kmh: int) -> None:
        """
        Simulate driving a given distance at a given speed.

        Args:
            distance_km: Distance in kilometers to drive.
            speed_kmh: Speed in kilometers per hour. Must be > 0.
        """
        if distance_km < 0:
            raise ValueError("distance_km must be >= 0")
        if speed_kmh <= 0:
            raise ValueError("speed_kmh must be > 0")

        print(f"{self.brand} {self.model} [{self.color}] started journey...")
        for km in range(1, distance_km + 1):
            sleep(60 / speed_kmh)
            print(f"KM: {km}")
        print(f"{self.brand} {self.model} [{self.color}] completed journey...")


# Homework #2: Bank to store money from sales
@dataclass(slots=True)
class Bank:
    balance: float = 0.0

    def deposit(self, amount: float) -> None:
        if amount <= 0:
            raise ValueError("Deposit amount must be > 0")
        self.balance += amount

    def __str__(self) -> str:
        return f"{self.balance:.2f}"


# 2. Test that the car works
def test_car() -> None:
    volvo = Car("Volvo", "Red", 200)
    volvo.drive(6, 140)


def _ask_int(prompt: str) -> int | None:
    """Ask for an integer; return None if invalid."""
    raw = input(prompt).strip()
    try:
        return int(raw)
    except ValueError:
        return None


def _ask_float(prompt: str) -> float | None:
    """Ask for a float; return None if invalid."""
    raw = input(prompt).strip()
    try:
        return float(raw)
    except ValueError:
        return None


# 3. Create more cars
def create_cars(cars: list[Car]) -> None:
    # Everything is case-sensitive here
    brand = input("Enter the brand: ").strip()
    color = input("Enter the color: ").strip()

    model = _ask_int("Enter the model number: ")
    if model is None:
        print("Error, please enter model as digits only.")
        return

    amount = _ask_int("Enter the amount: ")
    if amount is None:
        print("Error, please enter amount as digits only.")
        return
    if amount <= 0:
        print("Amount must be a positive number.")
        return

    cars.extend(Car(brand, color, model) for _ in range(amount))
    print("Cars created!")


# 4. Display the stock
def display_stock(cars: list[Car]) -> None:
    car_tuples: list[tuple[str, str, int]] = [(car.brand, car.color, car.model) for car in cars]
    counter: Counter[tuple[str, str, int]] = Counter(car_tuples)

    if not counter:
        print("No cars in stock.")
        return

    # Fix ordering bug from original code: tuple is (brand, color, model)
    for (brand, color, model), count in counter.items():
        print(f"{brand} {model} [{color}]: {count} in stock")


def display_bank(bank: Bank) -> None:
    print(f"Bank balance: {bank} currency units")


# Homework #1: Sell cars (checks stock; only sells if enough)
def sell_cars(cars: list[Car], bank: Bank) -> None:
    brand = input("Enter the brand to sell: ").strip()
    color = input("Enter the color to sell: ").strip()

    model = _ask_int("Enter the model number to sell: ")
    if model is None:
        print("Error, please enter model as digits only.")
        return

    amount = _ask_int("Enter the amount to sell: ")
    if amount is None:
        print("Error, please enter amount as digits only.")
        return
    if amount <= 0:
        print("Amount must be a positive number.")
        return

    price = _ask_float("Enter the price per car: ")
    if price is None:
        print("Error, please enter price as a number.")
        return
    if price <= 0:
        print("Price must be a positive number.")
        return

    target = Car(brand, color, model)
    in_stock = cars.count(target)

    if in_stock < amount:
        print(f"Not enough stock. Requested: {amount}, Available: {in_stock}.")
        return

    # Remove exactly `amount` matching cars from the list
    remaining_to_remove = amount
    updated: list[Car] = []
    for car in cars:
        if car == target and remaining_to_remove > 0:
            remaining_to_remove -= 1
        else:
            updated.append(car)

    cars[:] = updated

    total = price * amount
    bank.deposit(total)
    print(f"Sold {amount}x {brand} {model} [{color}] for {total:.2f}.")
    display_bank(bank)


def main() -> None:
    cars: list[Car] = [
        Car("Volvo", "Red", 200),
        Car("Volvo", "Red", 200),
        Car("Toyota", "Green", 321),
    ]
    bank = Bank()

    print('Type: "create" to create cars, "sell" to sell cars, "display" to display stock, "bank" to display balance')
    while True:
        user_input = input("You: ").lower().strip()

        if user_input == "create":
            create_cars(cars)
        elif user_input == "sell":
            sell_cars(cars, bank)
        elif user_input == "display":
            display_stock(cars)
        elif user_input == "bank":
            display_bank(bank)
        else:
            print(f'Unknown command: "{user_input}"')


if __name__ == "__main__":
    main()
