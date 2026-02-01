from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
import re


# 1. Create the model
@dataclass(frozen=True, slots=True)
class Response:
    response: str
    words: frozenset[str]
    required_words: frozenset[str]

    @classmethod
    def from_dict(cls, data: dict) -> 'Response':
        return cls(
            response=str(data['response']),
            words=frozenset(w.lower() for w in data.get('words', [])),
            required_words=frozenset(w.lower() for w in data.get('required_words', [])),
        )


class Chatbot:
    _split_re = re.compile(r'\s+|[,;?!.-]\s*')

    def __init__(self, responses_path: str | Path = 'responses_homework.json') -> None:
        self.responses_path: Path = Path(responses_path)
        self.responses: list[Response] = self._load_responses()

    def _load_responses(self) -> list[Response]:
        with self.responses_path.open('r', encoding='utf-8') as file:
            data = json.load(file)
        return [Response.from_dict(item) for item in data]

    @classmethod
    def split_text(cls, text: str) -> list[str]:
        parts = cls._split_re.split(text.lower().strip())
        return [p for p in parts if p]

    def match_rating(self, text: str, response: Response) -> float:
        user_words = set(self.split_text(text))

        if not response.words:
            return 0.0

        score = sum(1 for word in user_words if word in response.words)
        percent_matched = score / len(response.words)

        if response.required_words and not response.required_words.issubset(user_words):
            return 0.0

        return percent_matched

    def get_response(self, text: str) -> str:
        best_response: Response | None = None
        best_score: float = 0.0

        for response in self.responses:
            score = self.match_rating(text, response)
            if score > best_score:
                best_score = score
                best_response = response

        if not best_response or best_score == 0:
            return 'I don\'t understand... [0%]'

        return f'{best_response.response} [{best_score:.0%}]'

    def run(self) -> None:
        while True:
            user_input = input('You: ').strip()

            if user_input.lower() in {'exit', 'quit'}:
                print('Bot: See you!')
                return

            print(f'Bot: {self.get_response(user_input)}')


def main() -> None:
    bot = Chatbot()
    bot.run()


if __name__ == '__main__':
    main()
