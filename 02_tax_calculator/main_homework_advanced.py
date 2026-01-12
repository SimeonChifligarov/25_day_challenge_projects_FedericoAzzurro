"""
Income Tax Calculator with Projections
--------------------------------------
Calculates yearly tax based on income and tax rate,
including projections for doubled and tripled income.
"""

SEPARATOR_WIDTH: int = 40


def calculate_tax(income: float, tax_rate: float) -> float:
    """Return the tax amount for a given income and tax rate."""
    return income * tax_rate


def display_header(title: str) -> None:
    """Display a formatted header."""
    print('=' * SEPARATOR_WIDTH)
    print(title)
    print('=' * SEPARATOR_WIDTH)


def display_tax_row(label: str, amount: float) -> None:
    """Display a formatted tax row."""
    print(f'{label:<28} ${amount:>10,.2f}')


def main() -> None:
    """Main program execution."""
    base_income: float = float(input('Enter your yearly income: '))
    tax_rate: float = float(input('Enter your tax rate percentage: ')) / 100

    base_tax: float = calculate_tax(base_income, tax_rate)
    double_tax: float = calculate_tax(base_income * 2, tax_rate)
    triple_tax: float = calculate_tax(base_income * 3, tax_rate)

    display_header('Income Tax Calculator')

    print(f'Base Income:              ${base_income:,.2f}')
    print(f'Tax Rate:                 {tax_rate:.0%}')
    print('-' * SEPARATOR_WIDTH)

    display_tax_row('Yearly Tax (Base):', base_tax)
    display_tax_row('Yearly Tax (Double):', double_tax)
    display_tax_row('Yearly Tax (Triple):', triple_tax)

    print('=' * SEPARATOR_WIDTH)


if __name__ == '__main__':
    main()
