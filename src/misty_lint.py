import sys
from collections import defaultdict
from pathlib import Path
from contextlib import contextmanager
from itertools import chain
from argparse import ArgumentParser
from typing import Any, Sequence

from misty import emit_tokens_with_lines
from misty.dsl import Rule, RuleApplier, RuleRunner, Token, Message, Fixable
from misty.rules import default_rules

class Linter:
    def __init__(self, filename):
        self.filename = Path(filename)
        self.rules: list[Rule] = []

    def add(self, rule):
        self.rules.append(rule)

    def matches(self, token: Token):
        self.matching_rules = [rule for rule in self.rules if rule.applies_to(token)]
        return any(self.matching_rules)

    def errors(self, token: Token) -> list[Message]:
        elem, (row, col), data = token
        errs: list[Message] = []
        for rule in self.matching_rules:
            rule_errs = rule.errors(token)
            if rule_errs:
                errs.extend(rule_errs)
        return errs

    def fixes(self, token: Token) -> Any:
        return list(
            filter(None,
                   (rule.fix(token) for rule in self.matching_rules
                    if isinstance(rule, Fixable))
            )
        )


def build_parser() -> ArgumentParser:
    parser = ArgumentParser(
        description="Runs a set of linters over the output.")
    parser.add_argument('filename', nargs='?', type=str, default='-')
    parser.add_argument('--auto-fix', '-A', action='store_true')
    parser.add_argument('--suggest', '-S', action='store_true') # TODO
    return parser

def consume(ioreadable) -> Sequence[Token]:
    return list(emit_tokens_with_lines(ioreadable))

def build_linter(args):
    """
    Return an instance of a class that can be used like this:
      obj.matches(token) -> bool, true if applicable to token
      obj.valid(token) -> bool, checks validity
      obj.message(token) -> returns an error message which is collected
      obj.fix(token) -> returns a Token (can do in-place) where the error is removed, if possible
    """
    path = Path(args.filename)
    linter = Linter(filename=path)
    for rule_cls in default_rules:
        rule = rule_cls()
        if rule.ignore(path): continue
        linter.add(rule)
    return linter

@contextmanager
def opener(filename):
    if filename == "-":
        yield sys.stdin
    else:
        with open(filename, 'r') as fp:
            yield fp

def main():
    parser = build_parser()
    args = parser.parse_args()

    if args.auto_fix and args.suggest:
        parser.error("Cannot use both auto-fix and suggest modes.")

    # linter = build_linter(args)
    fixes = defaultdict(list)
    # Difference: RuleRunner emits diagnostics but never touches nodes
    # TODO: exclude rules whose ignore() returns true on this path
    # processor = RuleRunner([cls() for cls in default_rules])
    # but RuleApplier actually rewrites nodes
    processor = RuleApplier([cls() for cls in default_rules])

    filename = args.filename
    with opener(filename) as stream:
        tokens = consume(stream)
        res = processor.apply(tokens)
        breakpoint()

    print(tokens)


if __name__ == "__main__":
    main()
