from argparse import ArgumentParser
from pathlib import Path
from sys import exit
from typing import Iterable
import tempfile
import json
import os

from guards.main.registry import ClassRegistry
from parse.parser import RichDocParser, Section
from parse.logger import RichDocLogger, ParseIssue, IssueLevel
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

class GuardLogger(RichDocLogger):
    def __init__(self):
        super().__init__("Guard")

    def format_message(self, message: str, issue: ParseIssue):
        match issue:
            case ParseIssue(component=component, location=str(location),
                line_number=int(line_number), column_number=int(column_number)):
                return f"{location}:{line_number}:{column_number} [{component}] {message}"
            case ParseIssue(component=component, location=str(location), line_number=int(line_number)):
                return f"{location}:{line_number} [{component}] {message}"
            case ParseIssue(component=component, location=str(location)):
                return f"{location} [{component}] {message}"

        return message

def guard_names(guards: list):
    return ", ".join(guard.__name__ for guard in guards)

def run_guards(guards: list, targets: Iterable[Path]):
    logger = GuardLogger()
    for target in targets:
        guards_to_run = [guard for guard in guards if guard.accept_path(target)]
        if not guards_to_run:
            # Early skip if no guards accept this path
            continue

        # TODO: RichDocParser may have raised some issues here, gather them
        doc = RichDocParser(logger).parse_file(target)
        if not doc:
            logger.log_fatal(f"Failed to parse file {target}")
            continue

        guards_to_run = [guard for guard in guards_to_run if guard.accept_frontmatter(doc.front_matter)]
        if not guards_to_run:
            # Skip if no guards accept this path after loading frontmatter
            continue

        print(f"Checking {target} with {guard_names(guards_to_run)}")

        for guard_cls in guards_to_run:
            guard = guard_cls()
            guard.logger = logger

            with logger.parsing_context(guard_cls.__name__, target.as_posix()):
                guard.validate_frontmatter(doc.front_matter)

                for section in doc.sections:
                    match section:
                        # NOTE: Maybe Guard.Base should do this dispatch?
                        case Section(start=start, id=ident, block=blocks.CardBlock() as block):
                            guard.validate_card(block)
                            if block.ast:
                                guard.validate_card_ast(block.ast, block)
                        case Section(start=start, id=ident, block=blocks.TextBlock() as block):
                            guard.validate_text(block)

                guard.finalize()

    success = any(issue.level == IssueLevel.ERROR or issue.level == IssueLevel.FATAL for issue in logger.issues)
    return success, logger.issues

def build_argparser():
    parser = ArgumentParser(
        prog='guardian',
        description="Run guards (linters) on a file or directory")

    parser.add_argument(dest='event_files', nargs='*', metavar='filename.md',
                        help='Filename or directory to check. If not specified, run on all files.')
    # parser.add_argument('-A', action='store_const', const=True, dest='auto', help="Fix errors automatically")
    # parser.add_argument('-a', action='store_const', const=True, dest='auto_dryrun', help="Like -A, but display changes, don't edit the files.")
    # parser.add_argument('-f', action='store_const', const=True, dest='filter_mode', help='Run in filter mode. Read stdin, write to stdout, never modify files')
    parser.add_argument('--ci', action='store_const', dest='ci', const=True, help='Simulate CI mode')
    #parser.add_argument('-L', metavar='LINTER', action='extend', dest='linters', nargs='+', help='Use the specified linters')
    #parser.add_argument('-E', '--emacs', action='store_const', dest='emacs', const=True, help='Disable some checks that are not suitable for Flycheck.')
    return parser

def main():
    plugins = ClassRegistry()
    plugins.load_from_path('src/guards/card', package_name = 'card_guards')
    plugins.load_from_path('src/guards/doc', package_name = 'doc_guards')
    plugins.load_from_path('src/guards/markup', package_name = 'markup_guards')

    parser = build_argparser()
    args = parser.parse_args()
    # TODO: Filter mode
    targets = expand_targets(args.event_files)
    guards = list(plugins.registry.values())

    success, issues = run_guards(guards, targets)
    if running_github_actions(args):
       fd, tmpname = tempfile.mkstemp(suffix='.json', prefix='guardian_lint')
       with os.fdopen(fd, 'w') as fp:
           fp.write(json.dumps(ci_format_issues(issues)))
       print_github_output('report_file', tmpname, dump_err = args.ci)
    else:
        exit(0 if success else 1)

def running_github_actions(args):
    return os.getenv('GITHUB_OUTPUT') or args.ci

def ci_format_issues(issues: list[ParseIssue]):
    return [
        {
            "path": issue.location,
            "message": issue.message
        } | ({ "line": issue.line_number } if issue.line_number else {})
        | (issue.context if issue.context else {})
        for issue in issues
    ]

def print_github_output(key: str, value: str, dump_err: bool = False):
    gh_output_filename = '/dev/stderr' if dump_err else os.getenv('GITHUB_OUTPUT')

    with open(gh_output_filename, 'a') as fp:
        fp.write(f"{key}={value}\n")


if __name__ == "__main__":
    main()
