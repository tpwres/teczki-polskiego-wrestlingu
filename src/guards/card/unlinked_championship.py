from pathlib import Path
from yaml import tokens as t
import re
from typing import Any

from guards.main.base import Base
from guards.main.replacer import Replacer
from guards.main.state_machine import CardStateMachine
from parse import blocks, parser as rbparser
from card import AdHocTeam, Match, NamedTeam, NamedParticipant

class UnlinkedChampionship(Base):
    """Like UnlinkedParticipant, but only looks at c: championship in match rows."""

    @classmethod
    def accept_path(cls, path: Path):
        return path.is_relative_to('content/e')

    @classmethod
    def accept_frontmatter(cls, frontmatter: dict[str, Any]) -> bool:
        template = frontmatter.get('template')
        return template == 'event_page.html'

    def __init__(self):
        super().__init__()
        self.replacer = Replacer().with_championship_links()

    def validate_card_ast(self, ast: list[t.Token], card: blocks.CardBlock):
        # If we don't have a names dict, exit immediately
        if self.replacer.empty():
            return

        replacements = []
        sm = CardStateMachine(ast, option_value=self.handle_option_value)
        for token, replacement in sm:
            if replacement:
                replacements.append((token, replacement))

        # Now, replacements is a pair of tuples of (orig, replacement)
        # From orig we can grab line number, and from replacement the suggested text
        # For autocorrect, a similar process applies but if there's no replacement
        # then we collect the original token. Then a yaml emitter can reconstitute the entire document.
        for orig, repl in replacements:
            line_number = orig.start_mark.line
            old_text = orig.value
            new_text = repl.value

            line = card[line_number + 1]
            if self.skip_lint_instruction(line):
                continue

            self.logger.log_error(f"Championship `{old_text}` should be linked as `{new_text}`",
                                  line_number = line_number + card.starting_line + 1)

    def handle_option_value(self, token: t.ScalarToken, option_key: str, text: str):
        if option_key != 'c':
            return

        titles = set(title for title in self.replacer.keys()
            if title in text and f"[{title}]" not in text)

        if not titles:
            return

        replaced = self.replacer.replace(text, titles, on_match=Replacer.LINK)
        return t.ScalarToken(value=replaced, plain=token.plain, start_mark=token.start_mark, end_mark=token.end_mark)
