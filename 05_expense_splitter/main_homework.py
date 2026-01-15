print("Welcome to Expense Splitter™!")

# 1. Get total bill (handle empty input)
while True:
    total_bill_input: str = input("1. Enter the total bill you would like to split: ").strip()
    if total_bill_input == "":
        print("Please enter a total bill amount (e.g., 42.50).")
        continue
    try:
        total_bill: float = float(total_bill_input)
    except ValueError:
        print("That doesn't look like a number. Try again (e.g., 42.50).")
        continue
    if total_bill < 0:
        print("The bill can't be negative. Try again.")
        continue
    break

# 2. Add participants (handle none added)
people: list[str] = []
print("2. Add participants (press Enter on an empty line when finished):")
while True:
    input_name: str = input("Name: ").strip().lower()
    if input_name == "":
        if len(people) == 0:
            print("You must add at least one participant.")
            continue
        break

    if input_name in people:
        print("That name is already listed. Please add a different name.")
    else:
        people.append(input_name)

# 3. Split bill (cannot exceed 100%)
print("3. Now, specify the percentage each person will pay.")
print('(Type "even" at any time to split the bill equally.)')

people_dict: dict[str, float] = {}
remaining_percent: float = 100.0

for person in people:
    while True:
        percent_input: str = input(f"[{remaining_percent:.0f}% remaining] {person.capitalize()}: ").strip().lower()

        if percent_input == "":
            percent_input = "0"

        if percent_input == "even":
            even_share: float = total_bill / len(people)
            for nested_person in people:
                people_dict[nested_person] = even_share
            remaining_percent = 0.0
            break

        try:
            percent: float = float(percent_input)
        except ValueError:
            print('Please enter a number (e.g., 25) or type "even".')
            continue

        if percent < 0:
            print("Percent cannot be negative.")
            continue

        if percent > remaining_percent:
            print(f"You only have {remaining_percent:.0f}% remaining. Enter a smaller amount.")
            continue

        people_dict[person] = (percent / 100.0) * total_bill
        remaining_percent -= percent
        break

    if remaining_percent == 0.0:
        break

# 4. Display the information
print("\n--- Split Summary ---")
for name, share in people_dict.items():
    print(f"{name.capitalize():10}: ${share:,.2f}")
print("---------------------")
