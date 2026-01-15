from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from typing import Callable

# ---------------------------- Configuration ----------------------------

CURRENCY_SYMBOL = "$"
EVEN_KEYWORD = "even"
DONE_KEYWORD = "done"
LIST_KEYWORD = "list"
REMOVE_PREFIX = "remove "  # e.g. "remove alice"

CENT = Decimal("0.01")
HUNDRED = Decimal("100")


# ------------------------------ Utilities ------------------------------

def normalize_number_text(text: str) -> str:
    """Normalize user numeric input (e.g., allow ',' as decimal separator)."""
    return text.strip().replace(",", ".")


def parse_decimal(text: str) -> Decimal:
    """Parse a Decimal from user input, raising ValueError on invalid values."""
    try:
        value = Decimal(normalize_number_text(text))
    except (InvalidOperation, ValueError) as exc:
        raise ValueError("Invalid number") from exc

    if not value.is_finite():
        raise ValueError("Number must be finite")

    return value


def format_money(amount: Decimal, currency: str = CURRENCY_SYMBOL) -> str:
    q = amount.quantize(CENT, rounding=ROUND_HALF_UP)
    return f"{currency}{q:,.2f}"


# ------------------------------ Domain --------------------------------

@dataclass(frozen=True)
class SplitResult:
    bill_total: Decimal
    percents_by_person: dict[str, Decimal]
    amounts_by_person: dict[str, Decimal]


# -------------------------- Prompt functions ---------------------------

def prompt_total_bill(input_fn: Callable[[str], str] = input) -> Decimal:
    """Prompt until the user enters a valid, non-negative bill amount."""
    while True:
        raw = input_fn("1. Enter the total bill you would like to split: ").strip()
        if raw == "":
            print("Please enter a total bill amount (e.g., 42.50).")
            continue

        try:
            bill = parse_decimal(raw)
        except ValueError:
            print("That doesn't look like a valid number. Try again (e.g., 42.50).")
            continue

        if bill < 0:
            print("The total bill cannot be negative. Try again.")
            continue

        return bill


def prompt_participants(input_fn: Callable[[str], str] = input) -> list[str]:
    """
    Prompt for participant names. Requires at least one.
    Supports:
      - Entering a name
      - 'list' to show current participants
      - 'remove <name>' to remove
      - 'done' or empty line (only allowed once at least one participant exists)
    """
    people: list[str] = []
    print("2. Add participants.")
    print(f'   - Type a name and press Enter')
    print(f'   - Type "{LIST_KEYWORD}" to show current list')
    print(f'   - Type "{REMOVE_PREFIX}<name>" to remove someone')
    print(f'   - Press Enter on an empty line or type "{DONE_KEYWORD}" when finished')

    while True:
        raw = input_fn("Name: ").strip()
        cmd = raw.lower()

        if cmd == "" or cmd == DONE_KEYWORD:
            if not people:
                print("You must add at least one participant.")
                continue
            return people

        if cmd == LIST_KEYWORD:
            if people:
                print("Participants:", ", ".join(p.capitalize() for p in people))
            else:
                print("No participants yet.")
            continue

        if cmd.startswith(REMOVE_PREFIX):
            to_remove = cmd[len(REMOVE_PREFIX):].strip()
            if not to_remove:
                print('Usage: remove <name>')
                continue
            if to_remove in people:
                people.remove(to_remove)
                print(f"Removed {to_remove.capitalize()}.")
            else:
                print(f"{to_remove.capitalize()} is not in the list.")
            continue

        name = cmd.strip()
        if name == "":
            print("Please enter a non-empty name.")
            continue
        if name in people:
            print("That name is already listed. Please add a different name.")
            continue

        people.append(name)


def prompt_percentages(
        people: list[str],
        input_fn: Callable[[str], str] = input,
) -> dict[str, Decimal]:
    """
    Prompt for each person's percentage, enforcing:
      - No negatives
      - Cannot exceed remaining
      - Total ends at exactly 100% by auto-assigning remaining to the last person
    Also supports typing 'even' at any time to split 100% evenly.
    """
    print("3. Specify the percentage each person will pay.")
    print(f'   - Press Enter for 0% (last person defaults to the remaining %)')
    print(f'   - Type "{EVEN_KEYWORD}" at any time to split evenly')

    remaining = HUNDRED
    percents: dict[str, Decimal] = {}

    for idx, person in enumerate(people):
        is_last = idx == len(people) - 1

        while True:
            prompt = f"[{remaining:.0f}% remaining] {person.capitalize()}: "
            raw = input_fn(prompt).strip().lower()

            if raw == EVEN_KEYWORD:
                even = (HUNDRED / Decimal(len(people)))
                # Make total exactly 100 by adjusting last person for any fractional remainder
                percents = {p: even for p in people}
                total = sum(percents.values(), Decimal("0"))
                if total != HUNDRED:
                    percents[people[-1]] += (HUNDRED - total)
                return percents

            if raw == "":
                if is_last:
                    percent = remaining
                else:
                    percent = Decimal("0")
            else:
                try:
                    percent = parse_decimal(raw)
                except ValueError:
                    print(f'Please enter a number (e.g., 25) or type "{EVEN_KEYWORD}".')
                    continue

            if percent < 0:
                print("Percent cannot be negative. Try again.")
                continue
            if percent > remaining:
                print(f"That exceeds the remaining {remaining:.0f}%. Try a smaller amount.")
                continue

            percents[person] = percent
            remaining -= percent
            break

    # At this point, remaining should be 0 because we auto-assign it to the last person
    # (but keep a small safety adjustment in case of Decimal input oddities).
    total = sum(percents.values(), Decimal("0"))
    if total != HUNDRED:
        percents[people[-1]] += (HUNDRED - total)

    return percents


# ------------------------- Calculation & Output ------------------------

def calculate_amounts(
        total_bill: Decimal,
        percents_by_person: dict[str, Decimal],
) -> dict[str, Decimal]:
    """
    Convert percentages to currency amounts (rounded to cents),
    then adjust the last person's amount so totals match exactly.
    """
    people = list(percents_by_person.keys())

    raw_amounts = {
        name: (total_bill * (percent / HUNDRED))
        for name, percent in percents_by_person.items()
    }
    rounded = {name: amt.quantize(CENT, rounding=ROUND_HALF_UP) for name, amt in raw_amounts.items()}

    rounded_sum = sum(rounded.values(), Decimal("0"))
    target = total_bill.quantize(CENT, rounding=ROUND_HALF_UP)
    diff = target - rounded_sum

    if people:
        rounded[people[-1]] = (rounded[people[-1]] + diff).quantize(CENT, rounding=ROUND_HALF_UP)

    return rounded


def print_summary(result: SplitResult) -> None:
    print("\n--- Split Summary ---")
    print(f"Total bill: {format_money(result.bill_total)}")
    print("Participants:", ", ".join(name.capitalize() for name in result.percents_by_person))
    print("\nBreakdown:")
    for name in result.amounts_by_person:
        pct = result.percents_by_person[name]
        amt = result.amounts_by_person[name]
        print(f"{name.capitalize():12} {pct:>6.2f}%  {format_money(amt)}")
    print("---------------------")


# -------------------------------- Main --------------------------------

def main() -> None:
    print("Welcome to Expense Splitter™!")
    total_bill = prompt_total_bill()
    people = prompt_participants()

    print("\nParticipants confirmed:", ", ".join(p.capitalize() for p in people))
    percents = prompt_percentages(people)

    amounts = calculate_amounts(total_bill, percents)
    result = SplitResult(bill_total=total_bill, percents_by_person=percents, amounts_by_person=amounts)
    print_summary(result)


if __name__ == "__main__":
    main()
