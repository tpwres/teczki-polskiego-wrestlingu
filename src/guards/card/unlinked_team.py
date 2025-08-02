from pathlib import Path
from yaml import tokens as t
from typing import Any

from guards.main.base import Base
from guards.main.state_machine import CardStateMachine
from guards.main.replacer import Replacer
from parse import blocks
from card import Match, NamedTeam

class UnlinkedTeam(Base):
    """Like UnlinkedTeam, but checks named teams only."""

    @classmethod
    def accept_path(cls, path: Path):
        return path.is_relative_to('content/e')

    @classmethod
    def accept_frontmatter(cls, frontmatter: dict[str, Any]) -> bool:
        template = frontmatter.get('template')
        return template == 'event_page.html'

    def __init__(self):
        super().__init__()
        self.replacer = Replacer().with_team_links()

    def validate_card_ast(self, ast: list[t.Token], card: blocks.CardBlock):
        if self.replacer.empty():
            return

        replacements = []
        sm = CardStateMachine(ast, match_opponent=self.handle_teams)
        for token, replacement in sm:
            if replacement:
                replacements.append((token, replacement))

        for orig, repl in replacements:
            line_number = orig.start_mark.line
            old_name = orig.value
            new_name = repl.value

            line = card[line_number + 1]
            if self.skip_lint_instruction(line):
                continue

            # TODO: Can we emit a suggested diff here?
            message = f"Team `{old_name}` should be linked as `{new_name}`"
            self.logger.log_error(message, line_number = line_number + card.starting_line + 1)


    def handle_teams(self, token: t.ScalarToken, text: str):
        to_replace = set()
        teams = Match.parse_partners(text.split('+')) # See Match.parse_opponents
        for team_or_member in teams:
            match team_or_member:
                case NamedTeam() as team if not team.link:
                    if team.team_name in self.replacer.keys():
                        to_replace.add(team.team_name)

        if not to_replace:
            return # Nothing to do

        replaced = self.replacer.replace(text, to_replace, on_match=Replacer.LINK)
        return t.ScalarToken(value=replaced, plain=token.plain, start_mark=token.start_mark, end_mark=token.end_mark)
