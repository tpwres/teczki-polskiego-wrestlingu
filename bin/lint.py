#! /usr/bin/env python3

from pathlib import Path
from argparse import ArgumentParser
from itertools import chain
from utils import parse_front_matter
from card import Card, Match
from sys import exit
from typing import Iterable
from dataclasses import dataclass

def maybe_expand_dir(path: Path):
    if path.is_dir():
        return path.glob('????-??-??-*.md')
    else:
        return [path.absolute()]


@dataclass
class UnlinkedParticipant:
    path: Path
    match_index: int
    name: str
    link: str

    def __str__(self):
        return "Match {}: replace {} with link {}".format(self.match_index + 1, self.name, self.link)

def analyze_matches(matches: Iterable[Match], names_with_articles: dict[str, Path], errors: list[object], path: Path):
    for m in matches:
        participants = list(m.all_names())
        unlinked_participants = [p for p in participants if p.link is None]
        # Unlinked participants are only flagged if a personal file already exists
        for up in unlinked_participants:
            article = names_with_articles.get(up.name)
            if not article: continue

            link = "[{}](@/w/{})".format(up.name, article.name)
            errors.append(UnlinkedParticipant(path, m.index, up.name, link))


def load_existing_name_articles() -> dict[str, Path]:
    cwd = Path.cwd()
    talent_dir = cwd / 'content/w'
    name_files = talent_dir.glob('*.md')
    names = {}
    for path in name_files:
        if path.name == '_index.md': continue
        with path.open('r') as fp:
            text = fp.read()
            front_matter = parse_front_matter(text)
            names[front_matter['title']] = path
            if extra := front_matter.get('extra'):
                for alias in extra.get('career_aliases', []):
                    names[alias] = path

    return names

def main(args):
    errors = []
    cwd = Path.cwd()

    if args.event_files:
        files_to_lint = chain.from_iterable(maybe_expand_dir(Path(f)) for f in args.event_files)
    else:
        files_to_lint = maybe_expand_dir(cwd / 'content/e')

    names_with_articles = load_existing_name_articles()

    for path in files_to_lint:
        file_errors = []
        with path.open() as fp:
            text = fp.read()
            card = Card(text)
            if matches := card.matches:
                analyze_matches(matches, names_with_articles, file_errors, path.relative_to(cwd))
            else:
                file_errors.append("Missing card")

        for ferr in file_errors:
            errors.append("[{}] {}".format(path.relative_to(cwd), ferr))

    if errors:
        for err in errors:
            print(err)
        return False

    return True


def build_argparser():
    parser = ArgumentParser(
        prog='lint',
        description="Run various lint tasks on event files")

    parser.add_argument(dest='event_files', nargs='*', metavar='filename.md',
                        help='Filename to check. If not specified, run on all event files.')
    return parser

if __name__ == "__main__":
    parser = build_argparser()
    args = parser.parse_args()
    if main(args):
        # No errors
        exit(0)
    else:
        exit(1)
