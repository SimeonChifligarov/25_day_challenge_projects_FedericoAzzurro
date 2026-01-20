import json
from typing import Optional

Rates = dict[str, float]
Conversions = dict[str, float]


def load_exchange_rates(filename: str = 'currencies.json') -> Rates:
    with open(filename, 'r', encoding='utf-8') as file:
        data = json.load(file)

    if not isinstance(data, dict) or not all(isinstance(k, str) for k in data):
        raise ValueError('currencies.json must be an object with string currency codes.')

    rates: Rates = {}
    for code, value in data.items():
        try:
            rate = float(value)
        except (TypeError, ValueError):
            raise ValueError(f'Rate for "{code}" must be a number.')
        if rate <= 0:
            raise ValueError(f'Rate for "{code}" must be > 0.')
        rates[code.upper()] = rate

    return rates


def instructions() -> None:
    print('1. Type <amount><CURRENCY>, e.g. 10USD or 10 USD, to convert a currency.')
    print('2. Type LIST to list available currencies.')
    print('3. Type HELP to see instructions again.')
    print('4. Type QUIT to exit.')


def parse_amount_and_code(user_input: str) -> Optional[tuple[float, str]]:
    cleaned = user_input.replace(' ', '').replace('-', '')
    if len(cleaned) < 4:
        return None

    code = cleaned[-3:].upper()
    amount_str = cleaned[:-3]

    try:
        amount = float(amount_str)
    except ValueError:
        return None

    return amount, code


def get_conversions(input_amount: float, input_currency_code: str, rates: Rates) -> Conversions:
    base_amount = input_amount / rates[input_currency_code]
    return {code: base_amount * rate for code, rate in rates.items()}


def display_conversions(input_amount: float, input_currency_code: str, conversions: Conversions) -> None:
    print(f'{input_amount:>16.2f} {input_currency_code}')
    print('-' * 20)
    for code in sorted(conversions.keys()):
        print(f'= {conversions[code]:>14.2f} {code}')
    print('-' * 20)


def convert(user_input: str, rates: Rates) -> None:
    parsed = parse_amount_and_code(user_input)
    if parsed is None:
        print(f'"{user_input}" is invalid. Try: "10USD" or "10 USD"')
        return

    input_amount, input_currency_code = parsed

    if input_currency_code not in rates:
        print(f'Currency code: "{input_currency_code}" is invalid.')
        return

    conversions = get_conversions(input_amount, input_currency_code, rates)
    display_conversions(input_amount, input_currency_code, conversions)


def main() -> None:
    instructions()
    exchange_rates = load_exchange_rates()

    while True:
        try:
            user_input = input('Convert: ').strip()
        except EOFError:
            print('\nExiting.')
            break

        if not user_input:
            continue

        command = user_input.upper().strip()
        if command == 'LIST':
            print(f"Available currencies: {', '.join(sorted(exchange_rates.keys()))}")
            continue
        if command == 'HELP':
            instructions()
            continue
        if command == 'QUIT':
            print('Exiting.')
            break

        convert(user_input, exchange_rates)


if __name__ == '__main__':
    main()
