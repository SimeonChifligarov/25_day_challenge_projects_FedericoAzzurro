# Get user input and calculate tax
base_income = float(input('Enter your yearly income: '))
tax_rate = float(input('Enter your tax rate percentage: ')) / 100

tax_base = base_income * tax_rate
tax_double = (base_income * 2) * tax_rate
tax_triple = (base_income * 3) * tax_rate

# Display the data
print('=' * 40)
print('Income Tax Calculator')
print('=' * 40)
print(f'Base Income:              ${base_income:,.2f}')
print(f'Tax Rate:                 {tax_rate:.0%}')
print('-' * 40)
print(f'Yearly Tax (Base):        ${tax_base:,.2f}')
print(f'Yearly Tax (Double):      ${tax_double:,.2f}')
print(f'Yearly Tax (Triple):      ${tax_triple:,.2f}')
print('=' * 40)
