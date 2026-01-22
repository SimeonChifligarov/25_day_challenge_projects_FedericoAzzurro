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

    def drive(self, distance: int, speed: int) -> None:
        print(f"{self.brand} {self.model} [{self.color}] started journey...")
        for i in range(1, distance + 1):
            sleep(60 / speed)
            print(f"KM: {i}")
        print(f"{self.brand} {self.model} [{self.color}] completed journey...")


# 2. Test that the car works
def test_car() -> None:
    volvo = Car("Volvo", "Red", 200)
    volvo.drive(6, 140)


def _ask_car_details() -> Car:
    # Everything is case-sensitive here (same as the original)
    brand = input("Enter the brand: ").strip()
    color = input("Enter the color: ").strip()
    model = int(input("Enter the model number: ").strip())
    return Car(brand, color, model)


def _ask_amount(prompt: str) -> int:
    amount = int(input(prompt).strip())
    if amount <= 0:
        raise ValueError("Amount must be positive.")
    return amount


# 3. Create more cars
def create_cars(cars: list[Car]) -> None:
    try:
        car = _ask_car_details()
        amount = _ask_amount("Enter the amount: ")

        cars.extend([car] * amount)
        print("Cars created!")
    except ValueError:
        print("Error, please enter numbers as digits only (and positive where needed).")


# 4. Display the stock
def display_stock(cars: list[Car]) -> None:
    counter: Counter[Car] = Counter(cars)

    if not counter:
        print("Stock is empty.")
        return

    for car, count in counter.items():
        print(f"{car.brand} {car.model} [{car.color}]: {count} in stock")


# Homework #1: Sell cars (must check stock and only sell if enough)
# Homework #2: Bank to store the money from sales
def sell_cars(cars: list[Car], bank: dict[str, int]) -> None:
    """
    Sells cars from stock if enough are available.
    Bank is a tiny "accounting" dict holding money in whole units.
    """
    try:
        car = _ask_car_details()
        amount = _ask_amount("Enter the amount to sell: ")
        price = _ask_amount("Enter price per car: ")

        in_stock = cars.count(car)
        if in_stock < amount:
            print(f"Not enough stock: requested {amount}, available {in_stock}.")
            return

        # Remove the sold cars
        for _ in range(amount):
            cars.remove(car)

        earned = amount * price
        bank["money"] += earned
        print(f"Sold {amount}x {car.brand} {car.model} [{car.color}] for {earned}.")
        print(f"Bank balance: {bank['money']}")
    except ValueError:
        print("Error, please enter numbers as digits only (and positive where needed).")


def main() -> None:
    cars: list[Car] = [
        Car("Volvo", "Red", 200),
        Car("Volvo", "Red", 200),
        Car("Toyota", "Green", 321),
    ]
    bank: dict[str, int] = {"money": 0}

    print('Type: "create" to create cars, "sell" to sell cars, and "display" to display current stock')
    while True:
        user_input = input("You: ").lower().strip()

        if user_input == "create":
            create_cars(cars)
        elif user_input == "sell":
            sell_cars(cars, bank)
        elif user_input == "display":
            display_stock(cars)
            print(f"Bank balance: {bank['money']}")
        else:
            print(f'Unknown command: "{user_input}"')


if __name__ == "__main__":
    main()
