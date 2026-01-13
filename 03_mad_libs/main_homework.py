def get_user_input(prompt: str) -> str:
    """
    Prompt the user for input and return the entered string.
    """
    return input(prompt).strip()


def create_story(
        name: str,
        adjective: str,
        place: str,
        animal: str,
        emotion: str,
        verb: str,
        object_name: str,
) -> str:
    """
    Create and return a formatted story using user-provided inputs.
    """
    return f"""
{name}'s Unexpected Journey

One sunny morning, {name} walked into a {adjective} {place}.
Suddenly, a wild {animal} appeared out of nowhere!
Feeling very {emotion}, {name} decided to {verb} using a {object_name}.
To everyone's surprise, the {animal} became friendly and followed {name} home.
It turned out to be a day {name} would never forget.
"""


def main() -> None:
    """
    Main program execution.
    """
    print("Welcome to the Interactive Story Generator!\n")

    name: str = get_user_input("Enter a name: ")
    adjective: str = get_user_input("Enter an adjective: ")
    place: str = get_user_input("Enter a place: ")
    animal: str = get_user_input("Enter an animal: ")
    emotion: str = get_user_input("Enter an emotion: ")
    verb: str = get_user_input("Enter a verb: ")
    object_name: str = get_user_input("Enter an object: ")

    story: str = create_story(
        name=name,
        adjective=adjective,
        place=place,
        animal=animal,
        emotion=emotion,
        verb=verb,
        object_name=object_name,
    )

    print("\nResult:")
    print(story)


if __name__ == "__main__":
    main()
