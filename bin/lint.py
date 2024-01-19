#! /usr/bin/env python3

from pathlib import Path
from argparse import ArgumentParser
from itertools import chain
from utils import parse_front_matter
from card import Card, Match
from sys import exit
from typing import Iterable
from dataclasses import dataclass
import yaml
from rewriter import Rewriter

def maybe_expand_dir(path: Path):
    if path.is_dir():
        return path.glob('????-??-??-*.md')
    else:
        return [path.absolute()]


class LintError:
    pass

@dataclass
class UnlinkedParticipant(LintError):
    path: Path
    match_index: int
    name: str
    link: str

    def __str__(self):
        return "Match {}: replace {} with link {}".format(self.match_index + 1, self.name, self.link)

    def message(self, file_root: Path):
        return "[{}] {}".format(self.path.relative_to(file_root), self)

    def supports_auto(self):
        return True

    def replace_entry_text(self, entry):
        match entry:
            case str() as s:
                return s.replace(self.name, self.link)
            case _:
                return entry

    def fixed_text(self, text):
        card = Card(self.path.open())
        if not card.matches: return None

        with self.path.open('r') as fp:
            card_lines = ''.join(fp.readlines()[card.line_start:card.line_end])
            rewriter = Rewriter(card_lines)
            rewriter.add_replacement(self.name, self.link)
            result = rewriter.rewrite()
            print(result)


@dataclass
class MissingCard(LintError):
    path: Path

    def message(self, file_root: Path):
        return "[{}] Missing card block {{% card() %}} .. {{% end %}}".format(self.path.relative_to(file_root))

    def supports_auto(self):
        return False

def analyze_matches(matches: Iterable[Match], names_with_articles: dict[str, Path], errors: list[LintError], path: Path):
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
        file_errors: list[LintError] = []
        with path.open() as fp:
            text = fp.read()
            card = Card(text)
            if matches := card.matches:
                analyze_matches(matches, names_with_articles, file_errors, path)
            else:
                file_errors.append(MissingCard(path))

        errors.extend(file_errors)

    if errors:
        for err in errors:
            print(err.message(cwd))

            if args.auto or args.auto_dryrun and err.supports_auto():
                with err.path.open() as fp:
                    text = fp.read()
                    fixed_text = err.fixed_text(text)
                    if args.auto_dryrun:
                        print(fixed_text)

        return False

    return True


def build_argparser():
    parser = ArgumentParser(
        prog='lint',
        description="Run various lint tasks on event files")

    parser.add_argument(dest='event_files', nargs='*', metavar='filename.md',
                        help='Filename to check. If not specified, run on all event files.')
    parser.add_argument('-A', action='store_const', const=True, dest='auto', help="Fix errors automatically")
    parser.add_argument('-a', action='store_const', const=True, dest='auto_dryrun', help="Like -A, but display changes, don't edit the files.")
    return parser

if __name__ == "__main__":
    parser = build_argparser()
    args = parser.parse_args()
    if main(args):
        # No errors
        exit(0)
    else:
        exit(1)
