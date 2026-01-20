import json


# 1. Load the data
def load_exchange_rates(path: str = "currencies.json") -> dict[str, float]:
    with open(path, "r", encoding="utf-8") as file:
        return json.load(file)


# 2. Create instructions
def instructions() -> None:
    print("1. Type <amount><CURRENCY>, e.g. 10USD, to convert a currency.")
    print("2. Type LIST to list available currencies.")
    print("3. Type QUIT to exit.")


def parse_amount_and_currency(user_input: str, rates: dict[str, float]) -> tuple[float, str] | None:
    user_input = user_input.strip().upper()

    currency_code = user_input[-3:]
    if currency_code not in rates:
        print(f'Currency code: "{currency_code}" is invalid.')
        return None

    try:
        amount = float(user_input[:-3])
    except ValueError:
        print(f'"{user_input}" is invalid. Try something like: "10AUD"')
        return None

    return amount, currency_code


# Homework part 1: return conversions as a dict
def get_conversions(amount: float, from_currency: str, rates: dict[str, float]) -> dict[str, float]:
    base_amount_usd = amount / rates[from_currency]  # USD is the base in the file
    return {code: base_amount_usd * rate for code, rate in rates.items()}


# Homework part 2: display converted data
def display_conversions(amount: float, from_currency: str, conversions: dict[str, float]) -> None:
    print(f"{round(amount, 2):>16} {from_currency}")
    print("-" * 20)
    for code, converted_amount in conversions.items():
        print(f"= {round(converted_amount, 2):>14} {code}")
    print("-" * 20)


def main() -> None:
    instructions()
    exchange_rates = load_exchange_rates()

    while True:
        user_input = input("Convert: ").strip().upper()

        if user_input == "LIST":
            print(f"Available currencies: {', '.join(exchange_rates.keys())}")
            continue
        if user_input == "QUIT":
            print("Exiting.")
            break

        parsed = parse_amount_and_currency(user_input, exchange_rates)
        if parsed is None:
            continue

        amount, from_currency = parsed
        conversions = get_conversions(amount, from_currency, exchange_rates)
        display_conversions(amount, from_currency, conversions)


if __name__ == "__main__":
    main()
