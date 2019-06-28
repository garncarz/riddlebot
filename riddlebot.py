#!/usr/bin/env python3

import itertools
import json
from pprint import pprint
import traceback
from urllib.parse import urljoin

import requests

URL = 'https://api.noopschallenge.com/riddlebot/start'
GH_LOGIN = 'garncarz'


class Answerer:

    riddle_path = None
    finished = False

    def __init__(self):
        self.session = requests.Session()

    def login(self):
        r = self.session.post(URL, json={'login': GH_LOGIN})
        ack = r.json()

        assert 'Hello from Riddlebot' in ack['message']
        self.riddle_path = ack['riddlePath']

    @property
    def url(self):
         return urljoin(URL, self.riddle_path)

    @property
    def qm(self):
        return self.q['message']

    def get_question(self):
        r = self.session.get(self.url)
        self.q = r.json()

        pprint(self.q)

    def answer(self):
        for fn in filter(lambda attr: attr.startswith('solve_'), dir(self)):
            try:
                answer = getattr(self, fn)()
                if answer:
                    print(f'My answer: {answer}')
                    break
            except Exception:
                print(f'Automated answering {fn} failed.')
                traceback.print_exc()

        else:
            answer = input('Answer: ')

        r = self.session.post(self.url, json={'answer': answer})
        ack = r.json()

        pprint(ack)

        self.riddle_path = ack['nextRiddlePath']

    def solve_reverse(self):
        if self.q['riddleType'] != 'reverse':
            return

        return self.q['riddleText'][::-1]

    def solve_rotate(self):
        if self.q['riddleType'] not in ['rot13', 'caesar', 'vigenere']:
            return

        char_range = ord('Z') - ord('A') + 1

        def anti_rotate(riddle_key):
            if not isinstance(riddle_key, list):
                riddle_key = [riddle_key]
            riddle_key = itertools.cycle(riddle_key)

            return ''.join([
                chr((ord(c) - ord('A') - next(riddle_key)) % char_range + ord('A')) if 'A' <= c <= 'Z'
                else c
                for c in self.q['riddleText']
            ])

        def evaluate(s):
            words = s.split()
            return words.count('A') + words.count('IN') + words.count('OF') \
                   + words.count('THE') * 2 + words.count('AND') * 2

        def find_possible_rotation(enc_word, dec_word):
            return [(ord(ec) - ord(dc)) % char_range for (ec, dc) in zip(enc_word, dec_word)]

        if self.q['riddleType'] == 'caesar' and 'riddleKey' not in self.q:
            results = [anti_rotate(shift) for shift in range(char_range)]
            results = map(lambda r: (r, evaluate(r)), results)
            results = list(filter(lambda r: r[1] > 0, results))
            results.sort(key=lambda r: r[1], reverse=True)
            print('Possible results:')
            pprint(results)
            return results[0][0]

        riddle_key = self.q.get('riddleKey', 13)

        return anti_rotate(riddle_key)


def main():
    a = Answerer()

    a.login()

    while not a.finished:
        a.get_question()
        a.answer()


if __name__ == '__main__':
    main()