import json

CMD_LIST = "LIST"
CMD_QUIT = "QUIT"


def load_exchange_rates(path: str = "currencies.json") -> dict[str, float]:
    with open(path, "r", encoding="utf-8") as file:
        rates: dict[str, float] = json.load(file)

    if "USD" not in rates or rates["USD"] != 1.0:
        raise ValueError('Expected "USD": 1.0 in currencies.json')

    return rates


def instructions() -> None:
    print("1. Type <amount><CURRENCY>, e.g. 10USD or 10 USD, to convert a currency.")
    print("2. Type LIST to list available currencies.")
    print("3. Type QUIT to exit.")


def parse_amount_and_currency(
        user_input: str, rates: dict[str, float]
) -> tuple[float, str] | None:
    cleaned = user_input.strip().upper().replace(" ", "").replace(",", ".")

    if len(cleaned) < 4:
        print('Invalid input. Use format like "10USD" or "10 USD".')
        return None

    currency_code = cleaned[-3:]
    amount_part = cleaned[:-3]

    if currency_code not in rates:
        print(f'Currency code: "{currency_code}" is invalid.')
        return None

    try:
        amount = float(amount_part)
    except ValueError:
        print(f'"{user_input}" is invalid. Try something like: "10USD"')
        return None

    return amount, currency_code


def get_conversions(amount: float, from_currency: str, rates: dict[str, float]) -> dict[str, float]:
    base_amount_usd = amount / rates[from_currency]  # USD is the base in the file
    return {code: base_amount_usd * rate for code, rate in rates.items()}


def display_conversions(amount: float, from_currency: str, conversions: dict[str, float]) -> None:
    print(f"{amount:>16.2f} {from_currency}")
    print("-" * 20)
    for code in sorted(conversions):
        print(f"= {conversions[code]:>14.2f} {code}")
    print("-" * 20)


def main() -> None:
    instructions()
    exchange_rates = load_exchange_rates()

    while True:
        user_input = input("Convert: ").strip().upper()

        if user_input == CMD_LIST:
            print(f"Available currencies: {', '.join(sorted(exchange_rates.keys()))}")
            continue
        if user_input == CMD_QUIT:
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
