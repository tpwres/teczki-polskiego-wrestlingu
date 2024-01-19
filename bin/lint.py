#! /usr/bin/env python3

from pathlib import Path
from argparse import ArgumentParser
from itertools import chain
from utils import parse_front_matter
from card import Card, Match
from sys import exit
from typing import Iterable
from dataclasses import dataclass
from rewriter import Rewriter, UpdateMatch

def maybe_expand_dir(path: Path):
    if path.is_dir():
        return path.glob('????-??-??-*.md')
    else:
        return [path.absolute()]


class LintError:
    pass

@dataclass
class ReplaceCard:
    text: str

    def apply_changes(self, path):
        with path.open('r') as fp:
            card_text = fp.read()
            card = Card(card_text)
            start_offset, end_offset = card.start_offset, card.end_offset
            fp.close()

            new_text = card_text[:start_offset] + self.text + card_text[end_offset:]
            with path.open('w') as fp:
                fp.write(new_text)
        return True



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

    def calculate_fix(self, text):
        card = Card(self.path.open())
        if not card.matches: return None

        with self.path.open() as fp:
            card_lines = fp.read()[card.start_offset:card.end_offset]
            rewriter = Rewriter(card_lines)
            rewriter.add_replacement(UpdateMatch(self.match_index, self.name, self.link))
            result = rewriter.rewrite()
            return ReplaceCard(result)


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
            card = Card(fp)
            if matches := card.matches:
                analyze_matches(matches, names_with_articles, file_errors, path)
            else:
                file_errors.append(MissingCard(path))

        errors.extend(file_errors)

    if not errors:
        return True

    for err in errors:
        print(err.message(cwd))

        if not (args.auto or args.auto_dryrun):
            continue

        if not err.supports_auto():
            continue

        with err.path.open('r+') as fp:
            text = fp.read()
            fix = err.calculate_fix(text)
            if args.auto_dryrun:
                print(fix)
                continue

            if fix.apply_changes(err.path):
                print("Fixed")

    return False


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
