# 1. Create a way to store the data
db: dict[str, int] = {}


# 2. Create an easy way to write system messages
def announcement(msg: str) -> None:
    print(f"System: {msg}")


# 3. Create the core functionality
def ask_quantity(prompt: str = "Enter a quantity: ") -> int:
    """Keep asking until the user enters a valid integer quantity."""
    while True:
        raw: str = input(prompt).strip()
        try:
            return int(raw)
        except ValueError:
            announcement("Error, please enter a valid number.")


def add_item() -> None:
    name: str = input("Enter an item: ").lower().strip()
    quantity: int = ask_quantity()
    db[name] = quantity
    announcement(f'Added "{name}" x {quantity}')


def remove_item() -> None:
    name: str = input("Enter an item: ").lower().strip()
    try:
        db.pop(name)
        announcement(f'Successfully removed "{name}"')
    except KeyError:
        announcement(f'"{name}" not found in groceries.')


def modify_item() -> None:
    name: str = input("Enter an item to modify: ").lower().strip()
    if name not in db:
        announcement(f'"{name}" not found in groceries.')
        return

    quantity: int = ask_quantity("Enter the new quantity: ")
    db[name] = quantity
    announcement(f'Updated "{name}" to x {quantity}')


def read_list() -> None:
    if not db:
        announcement("There are no groceries to display.")
        return

    print("-" * 20)
    for k, v in db.items():
        print(f"{k.capitalize()}: {v}")
    print("-" * 20)


# 4. Create a menu for the user
def display_options() -> None:
    print("Options:")
    print("0 - Display options")
    print("1 - Read list")
    print("2 - Add to list")
    print("3 - Remove from list")
    print("4 - Modify quantity")
    print("_")


# 5. Get user input
def get_option(option: str) -> None:
    try:
        converted: int = int(option)
    except ValueError:
        announcement("Error, please enter a valid option.")
        return

    if converted == 0:
        display_options()
    elif converted == 1:
        read_list()
    elif converted == 2:
        add_item()
    elif converted == 3:
        remove_item()
    elif converted == 4:
        modify_item()
    else:
        announcement("Unknown option. Enter 0 to display options.")


# 6. Start and loop the program
def main() -> None:
    display_options()
    while True:
        user_input: str = input("You: ")
        get_option(user_input)


if __name__ == "__main__":
    main()
