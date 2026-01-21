from __future__ import annotations

db: dict[str, int] = {}


def announcement(msg: str) -> None:
    print(f"System: {msg}")


def prompt_item_name(prompt: str = "Enter an item: ") -> str:
    """Read and normalize an item name from the user."""
    return input(prompt).lower().strip()


def prompt_positive_int(prompt: str) -> int:
    """
    Prompt the user for an integer quantity.
    Retries immediately on invalid input (homework #1).
    """
    while True:
        raw: str = input(prompt).strip()
        try:
            value: int = int(raw)
        except ValueError:
            announcement("Error, please enter a valid number.")
            continue

        if value < 0:
            announcement("Error, quantity cannot be negative.")
            continue

        return value


def add_item() -> None:
    name: str = prompt_item_name()
    quantity: int = prompt_positive_int("Enter a quantity: ")

    db[name] = quantity
    announcement(f'Added "{name}" x {quantity}')


def remove_item() -> None:
    name: str = prompt_item_name()
    try:
        db.pop(name)
        announcement(f'Successfully removed "{name}"')
    except KeyError:
        announcement(f'"{name}" not found in groceries.')


def modify_item_quantity() -> None:
    """Modify the quantity of an existing item (homework #2)."""
    if not db:
        announcement("There are no groceries to modify.")
        return

    name: str = prompt_item_name("Enter an item to modify: ")
    if name not in db:
        announcement(f'"{name}" not found in groceries.')
        return

    old_qty: int = db[name]
    new_qty: int = prompt_positive_int(f'Enter a new quantity for "{name}" (current: {old_qty}): ')
    db[name] = new_qty
    announcement(f'Updated "{name}" from {old_qty} to {new_qty}')


def read_list() -> None:
    if not db:
        announcement("There are no groceries to display.")
        return

    print("-" * 20)
    for item, qty in db.items():
        print(f"{item.capitalize()}: {qty}")
    print("-" * 20)


def display_options() -> None:
    print("Options:")
    print("0 - Display options")
    print("1 - Read list")
    print("2 - Add to list")
    print("3 - Remove from list")
    print("4 - Modify item quantity")
    print("_")


def get_option(option: str) -> None:
    try:
        converted: int = int(option)
    except ValueError:
        announcement("Error, please enter a valid option.")
        return

    match converted:
        case 0:
            display_options()
        case 1:
            read_list()
        case 2:
            add_item()
        case 3:
            remove_item()
        case 4:
            modify_item_quantity()
        case _:
            announcement("Unknown option. Enter 0 to see options.")


def main() -> None:
    display_options()
    while True:
        user_input: str = input("You: ")
        get_option(user_input)


if __name__ == "__main__":
    main()
