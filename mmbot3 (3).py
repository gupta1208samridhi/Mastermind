import requests as rq
from typing import Self
import random
DEBUG = False

class MMBot:
    words = [word.strip() for word in open("words.txt")]
    mm_url = "https://we6.talentsprint.com/wordle/game/"
    register_url = mm_url + "register"
    creat_url = mm_url + "create"
    guess_url = mm_url + "guess"
    mode = "mastermind"

    def __init__(self: Self, name: str):
        def is_unique(w: str) -> bool:
            return len(w) == len(set(w))

        self.session = rq.session()
        register_dict = {"mode": self.mode, "name": name}
        reg_resp = self.session.post(MMBot.register_url, json=register_dict)
        self.me = reg_resp.json()['id']
        creat_dict = {"id": self.me, "overwrite": True}
        self.session.post(MMBot.creat_url, json=creat_dict)

        self.choices = [w for w in MMBot.words[:] if is_unique(w)]
        random.shuffle(self.choices)

    def play(self: Self) -> str:
        def post(choice: str) -> tuple[int, bool]:
            guess = {"id": self.me, "guess": choice}
            response = self.session.post(MMBot.guess_url, json=guess)
            rj = response.json()
            right = int(rj["feedback"])
            status = "win" in rj["message"]
            return right, status

        choice = random.choice(self.choices)
        self.choices.remove(choice)
        right, won = post(choice)
        tries = [f'{choice}:{right}']

        while not won:
            if DEBUG:
                print(choice, right, self.choices[:10])
            self.update(choice, right)
            choice = random.choice(self.choices)
            self.choices.remove(choice)
            right, won = post(choice)
            tries.append(f'{choice}:{right}')
        print("Secret is", choice, "found in", len(tries), "attempts")
        print("Route is:", " => ".join(tries))

    def update(self: Self, choice: str, right: int):
        def common(choice: str, word: str):
            return len(set(choice) & set(word))
        self.choices = [w for w in self.choices if common(choice, w) == right]


class WordleBot(MMBot):
    mode = "wordle"

    def __init__(self: Self, name: str):
        super().__init__(name)
        self.choices = [w for w in self.words[:]]

    def play(self: Self) -> str:
        def post(choice: str) -> tuple[str, bool, bool, str]:
            guess = {"id": self.me, "guess": choice}
            response = self.session.post(MMBot.guess_url, json=guess)
            rj = response.json()
            feedback = rj["feedback"]
            won = "win" in rj["message"]
            lost = "exceeded" in rj["message"]
            return feedback, won, lost, rj["answer"] if lost else ''

        choice = random.choice(self.choices)
        self.choices.remove(choice)
        feedback, won, lost, answer = post(choice)
        tries = [f'{choice}:{feedback}']

        while not (won or lost):
            if DEBUG:
                print(choice, feedback, self.choices[:10])
            self.update(choice, feedback)
            choice = random.choice(self.choices)
            self.choices.remove(choice)
            feedback, won, lost, answer = post(choice)
            tries.append(f'{choice}:{feedback}')
        if won:
            print("Secret is", choice, "found in", len(tries), "attempts")
        else:
            print(f"Lost; latest feedback was {feedback}; correct answer was {answer}")
        print("Route is:", " => ".join(tries))
    
    def update(self: Self, choice: str, feedback: str):
        def match_exact(words: list[str], letter: str, pos: int):
            return [word for word in words if word[pos] == letter]
        def match_exists(words: list[str], letter: str, pos: int):
            return [word for word in words if letter in word and word[pos] != letter]
        def match_not_contains(words: list[str], letter: str, pos: int):
            return [word for word in words if letter not in word]
        
        filters = {'R': match_not_contains, 'Y': match_exists, 'G': match_exact}

        for pos, (ch, fb) in enumerate(zip(choice, feedback)):
            self.choices = filters[fb](self.choices, ch, pos)



game = WordleBot("CodeShifu")
game.play()

