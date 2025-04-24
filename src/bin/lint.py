#! /usr/bin/env python3

import tomllib
from pathlib import Path
from argparse import ArgumentParser
from itertools import chain
from typing import Optional, cast, Callable
from sys import exit
from linters.base import LintError, FileBackedDoc, StreamDoc, Linter
from linters.unlinked_participant import UnlinkedParticipantLinter
from linters.unlinked_name import UnlinkedNameLinter
from linters.unlinked_event import UnlinkedEventLinter
from linters.well_formed_event import WellFormedEventLinter
from linters.championship_updated import ChampionshipUpdatedLinter

known_linters = {
    'WellFormedEvent': WellFormedEventLinter,
    'UnlinkedParticipant': UnlinkedParticipantLinter,
    'ChampionshipUpdated': ChampionshipUpdatedLinter,
}

def lookup_linter(name, config, linter_options={}) -> Optional[Linter]:
    """Return an instance of linter by name."""
    if name in known_linters:
        return known_linters[name](config=config, linter_options=linter_options)

PathPredicate = Callable[[Path], bool]

def maybe_expand_dir(path: Path, predicate: Optional[PathPredicate] = None) -> list[Path]:
    """
    If the file path given is a directory, recursively find files that match
    a pattern for event files under it, and return the list. Otherwise,
    return a list with just the path given.
    """
    if not predicate:
        predicate = lambda _p: True

    if path.is_dir():
        return [p.absolute() for p in path.rglob('*.md') if predicate(path)]
    else:
        return [path.absolute()]

def lint_main(args):
    errors = []
    cwd = Path.cwd()

    config_file = (cwd / 'config.toml')
    config = tomllib.load(config_file.open('rb'))

    if args.event_files:
        files_to_lint = chain.from_iterable(maybe_expand_dir(Path(f)) for f in args.event_files)
    else:
        files_to_lint = maybe_expand_dir(cwd / 'content/e')

    error_relative_to = cwd if args.relative else None

    linter_options = {}
    if args.emacs:
        linter_options['wfe:skip-filename-check'] = True

    linters_to_run: list[Linter]
    if args.linters:
        linters_to_run = list(
            filter(None,
                   (lookup_linter(name, config, linter_options) for name in args.linters)
        ))
    else:
        linters_to_run = cast(list[Linter], [
            lookup_linter('UnlinkedParticipant', config, linter_options),
            # lookup_linter('WellFormedEvent', config, linter_options)
        ])

    for path in files_to_lint:
        doc = FileBackedDoc(path)
        file_errors: list[LintError] = []

        for linter in linters_to_run:
            if not linter.handles(path):
                continue

            linter.reset()
            file_errors.extend(linter.lint(doc))

        errors.extend(file_errors)

    if not errors:
        return True

    success = True

    for err in errors:
        if err.fatal: success = False

        print(err.message(error_relative_to))

        if not (args.auto or args.auto_dryrun):
            continue

        if not err.supports_auto:
            continue

        with err.path.open('r+') as fp:
            text = fp.read()
            fix = err.calculate_fix(text)
            if args.auto_dryrun:
                print(fix)
                continue

            if fix.apply_changes(err.path):
                print("Fixed")

    return success

def filter_main():
    cwd = Path.cwd()

    config_file = (cwd / 'config.toml')
    config = tomllib.load(config_file.open('rb'))

    linters_to_run = [
        UnlinkedParticipantLinter(config),
        UnlinkedNameLinter(config),
        UnlinkedEventLinter(config)
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
                        help='''Filename to check. If not specified, run on all event files.
                                If passed a directory, check all files under it recursively.''')
    parser.add_argument('-A', action='store_const', const=True,
                        dest='auto', help="Fix errors automatically")
    parser.add_argument('-a', action='store_const', const=True,
                        dest='auto_dryrun', help="Like -A, but display changes, don't edit the files.")
    parser.add_argument('-f', action='store_const', const=True,
                        dest='filter_mode', help='Run in filter mode. Read stdin, write to stdout, never modify files')
    parser.add_argument('-L', metavar='LINTER', action='extend',
                        dest='linters', nargs='+', help='Use the specified linters')
    parser.add_argument('-r', '--relative', action='store_const',
                        dest='relative', const=True, help='Show error file paths relative to cwd')
    parser.add_argument('-E', '--emacs', action='store_const',
                        dest='emacs', const=True, help='Disable some checks that are not suitable for Flycheck.')
    return parser

def main():
    parser = build_argparser()
    args = parser.parse_args()
    if args.filter_mode:
        result = filter_main()
    else:
        result = lint_main(args)

    exit(0 if result else 1)

if __name__ == "__main__":
    main()

