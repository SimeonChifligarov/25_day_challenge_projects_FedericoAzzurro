import json


# 1. Load the data
def load_exchange_rates() -> dict[str, float]:
    with open('currencies.json', 'r', encoding='utf-8') as file:
        return json.load(file)


# 2. Create instructions
def instructions() -> None:
    print('1. Type <amount><CURRENCY>, e.g. 10USD, to convert a currency.')
    print('2. Type LIST to list available currencies.')
    print('3. Type QUIT to exit.')


def get_conversions(input_amount: float, input_currency_code: str, rates: dict[str, float]) -> dict[str, float]:
    """
    Return conversions for `input_amount` in `input_currency_code` to all currencies in `rates`.

    `rates` are assumed to be relative to a base currency (USD in the provided file).
    """
    base_amount: float = input_amount / rates[input_currency_code]
    return {currency_code: base_amount * rate for currency_code, rate in rates.items()}


def display_conversions(input_amount: float, input_currency_code: str, conversions: dict[str, float]) -> None:
    print(f'{round(input_amount, 2):>16} {input_currency_code}')
    print('-' * 20)
    for currency_code, converted_amount in conversions.items():
        print(f'= {round(converted_amount, 2):>14} {currency_code}')
    print('-' * 20)


def convert(user_input: str, rates: dict[str, float]) -> None:
    # Prepare data
    currency_codes: list[str] = list(rates.keys())
    input_currency_code: str = user_input[-3:]  # Gets the last three characters of a string

    # Check whether the user specifies a valid currency
    if input_currency_code not in currency_codes:
        print(f'Currency code: "{input_currency_code}" is invalid.')
        return

    # Check whether the specifies a valid amount
    try:
        input_amount: float = float(user_input[:-3])  # Gets everything besides the last three characters
    except ValueError:
        print(f'"{user_input}" is invalid. Try something like: "10AUD"')
        return

    conversions: dict[str, float] = get_conversions(input_amount, input_currency_code, rates)
    display_conversions(input_amount, input_currency_code, conversions)


def main() -> None:
    # 1. Display instructions
    instructions()

    # 2. Load exchange rate data
    exchange_rates: dict[str, float] = load_exchange_rates()

    # 3. Run
    while True:
        user_input: str = input('Convert: ').upper().strip()

        if user_input == 'LIST':
            available: str = ', '.join(exchange_rates.keys())
            print(f'Available currencies: {available}')
            continue
        if user_input == 'QUIT':
            print('Exiting.')
            break

        convert(user_input, exchange_rates)


if __name__ == '__main__':
    main()
