from typing import Final
import random

# Add parameters
LOWER_LIMIT: Final[int] = 0
UPPER_LIMIT: Final[int] = 100
random_number: int = random.randint(LOWER_LIMIT, UPPER_LIMIT)

# Score keeping
tries: int = 0


# Easy printing for what the bot says
def bot_message(msg: str) -> None:
    print(f'Bot: {msg}')


# Intro message
bot_message('Welcome to GuessThatNumber™!')
bot_message(f'Guess a number between {LOWER_LIMIT} & {UPPER_LIMIT}.')

# Infinite loop until user guesses
while True:
    # Validate user input so it doesn't crash the program
    try:
        user_guess: int = int(input('You: '))
    except ValueError as e:
        bot_message(f'{e}, please only use numbers.')
        continue

    # Count valid attempts
    tries += 1

    # Check user input against the number guessed
    if user_guess > random_number:
        bot_message('The number is lower.')
    elif user_guess < random_number:
        bot_message('The number is higher.')
    else:
        bot_message(f'You guessed correctly! You win in {tries} tries!')
        break
