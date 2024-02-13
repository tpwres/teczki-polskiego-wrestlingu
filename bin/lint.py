#! /usr/bin/env python3

from pathlib import Path
from argparse import ArgumentParser
from itertools import chain
from sys import exit
from linters.base import LintError
from linters.unlinked_participant import UnlinkedParticipantLinter
from linters.missing_card import MissingCardLinter
from linters.unlinked_name import UnlinkedNameLinter

def maybe_expand_dir(path: Path):
    if path.is_dir():
        return path.rglob('????-??-??-*.md')
    else:
        return [path.absolute()]

def main(args):
    errors = []
    cwd = Path.cwd()

    if args.event_files:
        files_to_lint = chain.from_iterable(maybe_expand_dir(Path(f)) for f in args.event_files)
    else:
        files_to_lint = maybe_expand_dir(cwd / 'content/e')

    linters_to_run = [
        MissingCardLinter(),
        UnlinkedParticipantLinter(),
        UnlinkedNameLinter(),
    ]

    for path in files_to_lint:
        file_errors: list[LintError] = []

        for linter in linters_to_run:
            file_errors.extend(linter.lint(path))

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
