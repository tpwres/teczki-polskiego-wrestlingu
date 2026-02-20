#! /usr/bin/env python3

import argparse
from content import ZipContentTree, FilesystemTree
from page import all_talent_pages
from card import names_in_match
from typing import cast, Any
from pathlib import Path
import json

def process(content, output_dir):
    aliases = {}

    all_event_pages = (content.page(pageio) for pageio in content.glob('content/e/**/????-??-??-*.md'))
    for page in all_event_pages:
        card = page.card
        if not card: continue

        for mm in card.matches:
            names = names_in_match(mm)

            for person in names:
                if person.link:
                    aliases[person.name] = clean_link(person.link)

        if not card.crew: continue
        for person in card.crew.members:
            if person.link:
                aliases[person.name] = clean_link(person.link)

    save_as_json(aliases, output_dir / 'aliases.json')


def clean_link(link: str) -> str:
    return link.replace('@/', '')

def save_as_json(data: Any, path: Path):
    with path.open('w') as fp:
        json.dump(data, fp)

if __name__ == "__main__":
    cwd = Path.cwd()
    parser = argparse.ArgumentParser(prog='build-metadata')
    parser.add_argument('-z', '--zipfile')
    args = parser.parse_args()
    if args.zipfile:
        content = ZipContentTree(Path(args.zipfile.strip()))
    else:
        content = FilesystemTree(cwd)

    output_dir = cwd / 'data'

    process(content, output_dir)
