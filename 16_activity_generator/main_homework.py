import json
from dataclasses import dataclass


# 1. Model the data
@dataclass
class Activity:
    activity: str
    activity_type: str
    cost: int
    people: int


# 2. Load the data
def load_data() -> list[Activity]:
    activities: list[Activity] = []
    with open('activities_homework.json', encoding='utf-8') as f:
        for activity in json.load(f):
            activities.append(
                Activity(
                    activity['activity'],
                    activity['type'],
                    activity['cost'],
                    activity['people'],
                )
            )

    return activities


def normalize_place(place: str) -> str | None:
    place = place.strip().lower()
    if place in ('any', ''):
        return None
    if place in ('indoor', 'outdoor'):
        return place
    return None


# 3. Generate activities
def generate_activities(activities: list[Activity]) -> None:
    try:
        people: int = int(input('How many people are you? '))
        cost: int = int(input('How much are you willing to spend per person ($)? '))
    except ValueError:
        print('Error: Please only enter numerical values.')
        return

    place_raw: str = input('Do you want indoor, outdoor, or any? (indoor/outdoor/any): ')
    place: str | None = normalize_place(place_raw)

    # Gather the activities that meet the criteria and display them
    matched_activities: list[Activity] = []
    for activity in activities:
        if activity.cost > cost:
            continue
        if activity.people > people:
            continue
        if place is not None and activity.activity_type != place:
            continue

        matched_activities.append(activity)

    if matched_activities:
        for i, matched in enumerate(matched_activities, 1):
            total_cost: int = people * matched.cost
            print(f'{i}: {matched.activity}: {matched.cost}$ per person [{people}p: {total_cost}$]')
    else:
        print('No activities matched your criteria...')


# 4. Put it all together
def main() -> None:
    activities: list[Activity] = load_data()
    generate_activities(activities)


if __name__ == '__main__':
    main()
