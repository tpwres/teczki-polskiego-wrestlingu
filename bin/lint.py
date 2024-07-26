#! /usr/bin/env python3

from pathlib import Path
from argparse import ArgumentParser
from itertools import chain
from sys import exit
from linters.base import LintError, FileBackedDoc, StreamDoc
from linters.unlinked_participant import UnlinkedParticipantLinter
from linters.missing_card import MissingCardLinter
from linters.unlinked_name import UnlinkedNameLinter
from linters.unlinked_event import UnlinkedEventLinter
from linters.well_formed_event import WellFormedEventLinter

known_linters = {
    'WellFormedEvent': WellFormedEventLinter,
    'UnlinkedParticipant': UnlinkedParticipantLinter,
    'MissingCard': MissingCardLinter, # To be replaced by WFE
}

def lookup_linter(name) -> object:
    if name in known_linters:
        return known_linters[name]()

def maybe_expand_dir(path: Path):
    if path.is_dir():
        return [p.absolute() for p in path.rglob('????-??-??-*.md')]
    else:
        return [path.absolute()]

def lint_main(args):
    errors = []
    cwd = Path.cwd()

    if args.event_files:
        files_to_lint = chain.from_iterable(maybe_expand_dir(Path(f)) for f in args.event_files)
    else:
        files_to_lint = maybe_expand_dir(cwd / 'content/e')

    if args.linters:
        linters_to_run = filter(None, (lookup_linter(name) for name in args.linters))
    else:
        linters_to_run = [
            lookup_linter('MissingCard'),
            lookup_linter('UnlinkedParticipant')
        ]

    for path in files_to_lint:
        doc = FileBackedDoc(path)
        file_errors: list[LintError] = []

        for linter in linters_to_run:
            file_errors.extend(linter.lint(doc))

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

def filter_main():
    linters_to_run = [
        UnlinkedParticipantLinter(),
        UnlinkedNameLinter(),
        UnlinkedEventLinter()
    ]
    errors = []

    io = StreamDoc()
    for linter in linters_to_run:
        errors.extend(linter.lint(io))

    if not errors:
        io.dump()
        return True

    # Never print errors, always auto-fix them
    for err in errors:
        if not err.supports_auto():
            continue

        with err.path.open('r+') as fp:
            text = fp.read()
            fix = err.calculate_fix(text)
            fix.apply_changes(err.path)

    io.dump()
    return False

def build_argparser():
    parser = ArgumentParser(
        prog='lint',
        description="Run various lint tasks on event files")

    parser.add_argument(dest='event_files', nargs='*', metavar='filename.md',
                        help='Filename to check. If not specified, run on all event files.')
    parser.add_argument('-A', action='store_const', const=True, dest='auto', help="Fix errors automatically")
    parser.add_argument('-a', action='store_const', const=True, dest='auto_dryrun', help="Like -A, but display changes, don't edit the files.")
    parser.add_argument('-f', action='store_const', const=True, dest='filter_mode', help='Run in filter mode. Read stdin, write to stdout, never modify files')
    parser.add_argument('-L', metavar='LINTER', action='extend', dest='linters', nargs='+', help='Use the specified linters')
    return parser

if __name__ == "__main__":
    parser = build_argparser()
    args = parser.parse_args()
    if args.filter_mode:
        result = filter_main()
    else:
        result = lint_main(args)

    exit(0 if result else 1)
