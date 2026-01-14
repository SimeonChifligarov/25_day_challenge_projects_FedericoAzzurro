import random

# Game symbols
symbols: dict[str, str] = {
    'rock': '🪨',
    'paper': '📄',
    'scissors': '✂️',
}

valid_choices = tuple(symbols) + ('quit',)

while True:
    # Get user input
    player_choice: str = input(
        'Choose rock (🪨), paper (📄), scissors (✂️), or quit: '
    ).strip().lower()

    # Handle quit
    if player_choice == 'quit':
        print('Goodbye! 👋')
        break

    # Handle invalid input
    if player_choice not in symbols:
        print('Invalid choice. Please try again.\n')
        continue

    computer_choice: str = random.choice(tuple(symbols))

    # Display choices
    print('\nResults')
    print('----------------')
    print(f'You:      {symbols[player_choice]}  {player_choice}')
    print(f'Computer: {symbols[computer_choice]}  {computer_choice}')
    print('----------------')

    # Determine the winner
    if player_choice == computer_choice:
        print("It's a tie!")
    elif player_choice == 'rock' and computer_choice == 'scissors':
        print('You won with rock! 🪨')
    elif player_choice == 'paper' and computer_choice == 'rock':
        print('You won with paper! 📄')
    elif player_choice == 'scissors' and computer_choice == 'paper':
        print('You won with scissors! ✂️')
    else:
        print('Computer wins! 🤖')

    print()
