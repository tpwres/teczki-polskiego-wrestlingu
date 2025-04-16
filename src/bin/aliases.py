
#! /usr/bin/env python3

from page import all_event_pages
from card import names_in_match
from typing import Any
from pathlib import Path
import json

def main():
    aliases = {}

    for page in all_event_pages():
        card = page.card
        if not card:
            continue

        for mm in card.matches:
            names = names_in_match(mm)

            for person in names:
                if person.link:
                    aliases[person.name] = clean_link(person.link)

        if not card.crew:
            continue
        for person in card.crew.members:
            if person.link:
                aliases[person.name] = clean_link(person.link)

    save_as_json(aliases, Path('data/aliases.json'))


def clean_link(link: str) -> str:
    return link.replace('@/', '')

def save_as_json(data: Any, path: Path):
    with path.open('w') as fp:
        json.dump(data, fp)

if __name__ == "__main__":
    main()
