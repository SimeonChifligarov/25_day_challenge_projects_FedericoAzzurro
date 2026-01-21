from __future__ import annotations

from dataclasses import dataclass
from typing import Callable


# ----------------------------
# Data model
# ----------------------------
@dataclass(slots=True)
class GroceryItem:
    quantity: int
    note: str = ""
    purchased: bool = False


db: dict[str, GroceryItem] = {}


# ----------------------------
# Console helpers
# ----------------------------
def announcement(msg: str) -> None:
    print(f"System: {msg}")


def prompt_non_empty_name(prompt: str = "Enter an item: ") -> str:
    """Prompt until the user enters a non-empty item name."""
    while True:
        name: str = input(prompt).strip().lower()
        if name:
            return name
        announcement("Error, item name cannot be empty.")


def prompt_int(prompt: str) -> int:
    """Prompt until the user enters a valid integer."""
    while True:
        raw: str = input(prompt).strip()
        try:
            return int(raw)
        except ValueError:
            announcement("Error, please enter a valid number.")


def prompt_non_negative_int(prompt: str) -> int | None:
    """Prompt until the user enters a non-negative integer."""
    while True:
        value: int = prompt_int(prompt)
        if value < 0:
            announcement("Error, quantity cannot be negative.")
            continue
        return value


def prompt_choice(prompt: str, allowed: set[str]) -> str:
    """Prompt until the user enters an allowed choice (case-insensitive)."""
    allowed_lower = {x.lower() for x in allowed}
    while True:
        choice = input(prompt).strip().lower()
        if choice in allowed_lower:
            return choice
        announcement(f"Error, choose one of: {', '.join(sorted(allowed_lower))}")


# ----------------------------
# Pure business logic
# ----------------------------
def add_item_logic(items: dict[str, GroceryItem], name: str, qty: int, *, increment: bool) -> None:
    if name in items and increment:
        items[name].quantity += qty
    else:
        # Preserve existing metadata if we are overwriting
        if name in items:
            existing = items[name]
            items[name] = GroceryItem(quantity=qty, note=existing.note, purchased=existing.purchased)
        else:
            items[name] = GroceryItem(quantity=qty)


def remove_item_logic(items: dict[str, GroceryItem], name: str) -> bool:
    return items.pop(name, None) is not None


def set_quantity_logic(items: dict[str, GroceryItem], name: str, qty: int) -> bool:
    if name not in items:
        return False
    items[name].quantity = qty
    return True


def change_quantity_by_delta_logic(items: dict[str, GroceryItem], name: str, delta: int) -> tuple[bool, int]:
    """
    Returns (found, new_quantity).
    If item doesn't exist -> (False, 0).
    """
    if name not in items:
        return False, 0
    items[name].quantity += delta
    return True, items[name].quantity


def toggle_purchased_logic(items: dict[str, GroceryItem], name: str) -> bool:
    if name not in items:
        return False
    items[name].purchased = not items[name].purchased
    return True


def clear_list_logic(items: dict[str, GroceryItem]) -> None:
    items.clear()


# ----------------------------
# Features / actions
# ----------------------------
def read_list() -> None:
    if not db:
        announcement("There are no groceries to display.")
        return

    # improvement: show sorted for readability
    print("-" * 36)
    total_qty = 0
    purchased_count = 0

    for name in sorted(db):
        item = db[name]
        status = "✓" if item.purchased else " "
        note = f" ({item.note})" if item.note else ""
        print(f"[{status}] {name.capitalize():20} x {item.quantity}{note}")
        total_qty += item.quantity
        if item.purchased:
            purchased_count += 1

    print("-" * 36)
    announcement(
        f"Items: {len(db)} | Total quantity: {total_qty} | Purchased: {purchased_count}/{len(db)}"
    )


def add_item() -> None:
    name: str = prompt_non_empty_name()

    # improvement: don't overwrite by default when item exists
    increment = False
    if name in db:
        choice = prompt_choice(
            f'"{name}" already exists. (a)dd more or (s)et quantity? [a/s]: ',
            {"a", "s"},
        )
        increment = choice == "a"

    qty: int = prompt_non_negative_int("Enter a quantity: ")
    add_item_logic(db, name, qty, increment=increment)

    if increment:
        announcement(f'Added {qty} more to "{name}" (now {db[name].quantity}).')
    else:
        announcement(f'Set "{name}" quantity to {db[name].quantity}.')


def remove_item() -> None:
    if not db:
        announcement("There are no groceries to remove.")
        return

    name: str = prompt_non_empty_name()
    removed = remove_item_logic(db, name)
    if removed:
        announcement(f'Successfully removed "{name}".')
    else:
        announcement(f'"{name}" not found in groceries.')


def modify_item_quantity() -> None:
    """Improvement: multiple modify styles + optional remove on 0."""
    if not db:
        announcement("There are no groceries to modify.")
        return

    name: str = prompt_non_empty_name("Enter an item to modify: ")
    if name not in db:
        announcement(f'"{name}" not found in groceries.')
        return

    item = db[name]
    print(f'Current: "{name}" x {item.quantity}')

    mode = prompt_choice(
        "Choose: (s)et, (i)ncrease, (d)ecrease [s/i/d]: ",
        {"s", "i", "d"},
    )

    if mode == "s":
        new_qty = prompt_non_negative_int("Enter the new quantity: ")
        set_quantity_logic(db, name, new_qty)
        announcement(f'Updated "{name}" to {new_qty}.')
    else:
        amount = prompt_non_negative_int("Enter amount: ")
        delta = amount if mode == "i" else -amount
        _, new_qty = change_quantity_by_delta_logic(db, name, delta)

        # Optional behavior: auto-remove if <= 0
        if new_qty <= 0:
            removed = remove_item_logic(db, name)
            if removed:
                announcement(f'"{name}" quantity became {new_qty}; item removed from the list.')
            return

        announcement(f'Updated "{name}" to {new_qty}.')


def edit_item_note() -> None:
    """Small extension enabled by the dataclass model."""
    if not db:
        announcement("There are no groceries to edit.")
        return

    name: str = prompt_non_empty_name("Enter an item to add/edit a note for: ")
    if name not in db:
        announcement(f'"{name}" not found in groceries.')
        return

    note = input("Enter a note (leave empty to clear): ").strip()
    db[name].note = note
    announcement(f'Note updated for "{name}".')


def toggle_purchased() -> None:
    if not db:
        announcement("There are no groceries to toggle.")
        return

    name: str = prompt_non_empty_name("Enter an item to toggle purchased: ")
    ok = toggle_purchased_logic(db, name)
    if not ok:
        announcement(f'"{name}" not found in groceries.')
        return

    status = "purchased" if db[name].purchased else "not purchased"
    announcement(f'Marked "{name}" as {status}.')


def clear_list() -> None:
    """Improvement: clear list with confirmation."""
    if not db:
        announcement("There is nothing to clear.")
        return

    confirm = prompt_choice("Are you sure you want to clear the entire list? [y/n]: ", {"y", "n"})
    if confirm == "y":
        clear_list_logic(db)
        announcement("List cleared.")
    else:
        announcement("Clear cancelled.")


def exit_program() -> None:
    """Improvement: exit option."""
    announcement("Goodbye!")
    raise SystemExit(0)


# ----------------------------
# Menu & dispatcher
# ----------------------------
def display_options() -> None:
    print("Options:")
    print("0 - Display options / help")
    print("1 - Read list")
    print("2 - Add to list")
    print("3 - Remove from list")
    print("4 - Modify item quantity")
    print("5 - Edit item note")
    print("6 - Toggle purchased")
    print("7 - Clear list")
    print("9 - Exit")
    print("_")


ACTIONS: dict[int, Callable[[], None]] = {
    0: display_options,
    1: read_list,
    2: add_item,
    3: remove_item,
    4: modify_item_quantity,
    5: edit_item_note,
    6: toggle_purchased,
    7: clear_list,
    9: exit_program,
}


def get_option(option: str) -> None:
    # improvement: "help" command + friendly unknown command handling
    cleaned = option.strip().lower()
    if cleaned in {"help", "h", "?"}:
        display_options()
        return

    try:
        converted: int = int(cleaned)
    except ValueError:
        announcement('Error, enter a number (or type "help").')
        display_options()
        return

    action = ACTIONS.get(converted)
    if action is None:
        announcement('Unknown option. Enter 0 (or "help") to see options.')
        display_options()
        return

    action()


def main() -> None:
    display_options()
    while True:
        user_input: str = input("You: ")
        get_option(user_input)


if __name__ == "__main__":
    main()
