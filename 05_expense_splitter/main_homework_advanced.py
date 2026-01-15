from __future__ import annotations


def prompt_total_bill() -> float:
    """Prompt until the user enters a valid, non-negative bill amount."""
    while True:
        raw = input("1. Enter the total bill you would like to split: ").strip()
        if raw == "":
            print("Please enter a total bill amount (e.g., 42.50).")
            continue

        try:
            bill = float(raw)
        except ValueError:
            print("That doesn't look like a number. Try again (e.g., 42.50).")
            continue

        if bill < 0:
            print("The total bill cannot be negative. Try again.")
            continue

        return bill


def prompt_participants() -> list[str]:
    """Prompt for participant names. Returns a non-empty list of unique names."""
    people: list[str] = []
    print("2. Add participants (press Enter on an empty line when finished):")

    while True:
        name = input("Name: ").strip().lower()
        if name == "":
            if not people:
                print("You must add at least one participant.")
                continue
            break

        if name in people:
            print("That name is already listed. Please add a different name.")
            continue

        people.append(name)

    return people


def prompt_split_amounts(total_bill: float, people: list[str]) -> dict[str, float]:
    """
    Prompt for each person's percentage.
    - Enter => 0%
    - 'even' => split remaining evenly across all people (simple behavior)
    - Enforces that total charged percentage never exceeds 100%.
    """
    print("3. Now, specify the percentage each person will pay.")
    print('(Press Enter for 0%. Type "even" at any time to split the bill equally.)')

    shares: dict[str, float] = {}
    remaining_percent = 100.0

    for person in people:
        while True:
            raw = input(f"[{remaining_percent:.0f}% remaining] {person.capitalize()}: ").strip().lower()

            if raw == "":
                percent = 0.0
            elif raw == "even":
                even_share = total_bill / len(people)
                return {p: even_share for p in people}
            else:
                try:
                    percent = float(raw)
                except ValueError:
                    print('Please enter a number (e.g., 25) or type "even".')
                    continue

            if percent < 0:
                print("Percent cannot be negative. Try again.")
                continue
            if percent > remaining_percent:
                print(f"That exceeds the remaining {remaining_percent:.0f}%. Try a smaller amount.")
                continue

            shares[person] = (percent / 100.0) * total_bill
            remaining_percent -= percent
            break

    return shares


def print_summary(shares: dict[str, float]) -> None:
    print("\n--- Split Summary ---")
    for name, share in shares.items():
        print(f"{name.capitalize():10}: ${share:,.2f}")
    print("---------------------")


def main() -> None:
    print("Welcome to Expense Splitter™!")
    total_bill = prompt_total_bill()
    people = prompt_participants()
    shares = prompt_split_amounts(total_bill, people)
    print_summary(shares)


if __name__ == "__main__":
    main()
