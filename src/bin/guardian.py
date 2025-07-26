from argparse import ArgumentParser
from pathlib import Path
from sys import exit
from typing import Iterable

from guards import card as card_guards
from parse.parser import RichDocParser, Section
from parse import blocks

def expand_targets(args):
    # Args is either empty, or a list of files and directories.
    # For directories, walk them recursively and emit pathnames of all .md files inside
    pattern = '*.md'
    if not args:
        for subpath in Path('content/').rglob(pattern):
            yield subpath

        return

    for arg in args:
        path = Path(arg)

        if path.is_dir():
            for subpath in path.rglob(pattern):
                yield subpath
        else:
            yield path

def load_guard_classes():
    guard_classes = [
        card_guards.ValidCard,
        card_guards.CardOptionsCorrect,
        card_guards.CreditsCorrect,
        card_guards.DelimitersCorrect,
        card_guards.SegmentDescription
    ]
    return guard_classes

def run_guards(guards: list, targets: Iterable[Path]):
    issues = []
    for target in targets:
        guards_to_run = [guard for guard in guards if guard.accept_path(target)]
        if not guards_to_run:
            # Early skip if no guards accept this path
            continue

        # TODO: RichDocParser may have raised some issues here, gather them
        doc = RichDocParser().parse_file(target)

        guards_to_run = [guard for guard in guards_to_run if guard.accept_frontmatter(doc.front_matter)]
        if not guards_to_run:
            # Skip if no guards accept this path after loading frontmatter
            continue

        print(f"Checking {target}")
        for guard_cls in guards_to_run:
            guard = guard_cls()

            guard.validate_frontmatter(doc.front_matter)

            for section in doc.sections:
                match section:
                    # NOTE: Maybe Guard.Base should do this dispatch?
                    case Section(start=start, id=ident, block=blocks.CardBlock() as block):
                        guard.validate_card(block)
                    case Section(start=start, id=ident, block=blocks.TextBlock() as block):
                        guard.validate_text(block)
                    case _:
                        breakpoint()
        break

def build_argparser():
    parser = ArgumentParser(
        prog='guardian',
        description="Run guards (linters) on a file or directory")

    parser.add_argument(dest='event_files', nargs='*', metavar='filename.md',
                        help='Filename to check. If not specified, run on all files.')
    parser.add_argument('-A', action='store_const', const=True, dest='auto', help="Fix errors automatically")
    parser.add_argument('-a', action='store_const', const=True, dest='auto_dryrun', help="Like -A, but display changes, don't edit the files.")
    parser.add_argument('-f', action='store_const', const=True, dest='filter_mode', help='Run in filter mode. Read stdin, write to stdout, never modify files')
    #parser.add_argument('-L', metavar='LINTER', action='extend', dest='linters', nargs='+', help='Use the specified linters')
    #parser.add_argument('-r', '--relative', action='store_const', dest='relative', const=True, help='Show error file paths relative to cwd')
    #parser.add_argument('-E', '--emacs', action='store_const', dest='emacs', const=True, help='Disable some checks that are not suitable for Flycheck.')
    return parser

def main():
    parser = build_argparser()
    args = parser.parse_args()
    # TODO: Filter mode
    targets = expand_targets(args.event_files)
    guards = load_guard_classes()

    success = run_guards(guards, targets)
    exit(0 if success else 1)

if __name__ == "__main__":
    main()
