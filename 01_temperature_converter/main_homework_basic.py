# Constants
MILES_TO_KILOMETERS = 1.60934
KILOMETERS_TO_MILES = 1 / MILES_TO_KILOMETERS

# User input
miles_input = 10
kilometers_input = 5

# Conversions
converted_to_km = miles_input * MILES_TO_KILOMETERS
converted_to_miles = kilometers_input * KILOMETERS_TO_MILES

# Display
print(f'{miles_input} miles -> {converted_to_km:.2f} km')
print(f'{kilometers_input} km -> {converted_to_miles:.2f} miles')
