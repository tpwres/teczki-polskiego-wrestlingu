from pathlib import Path
from yaml import tokens as t
from typing import Any

from guards.main.base import Base
from guards.main.state_machine import CardStateMachine
from guards.main.replacer import Replacer
from parse import blocks
from card import AdHocTeam, Match, NamedTeam, NamedParticipant

class UnlinkedCrewmember(Base):
    """Like UnlinkedParticipant, but only looks at credits row."""

    @classmethod
    def accept_path(cls, path: Path):
        return path.is_relative_to('content/e')

    @classmethod
    def accept_frontmatter(cls, frontmatter: dict[str, Any]) -> bool:
        template = frontmatter.get('template')
        return template == 'event_page.html'

    def __init__(self):
        super().__init__()
        self.replacer = Replacer().with_talent_names_from_metadata()


    def validate_card_ast(self, ast: list[t.Token], card: blocks.CardBlock):
        # If we don't have a names dict, exit immediately
        if self.replacer.empty():
            return

        replacements = []
        sm = CardStateMachine(ast, crew_entry=self.crew_entry)
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

            self.logger.log_error(f"Crew member line `{old_text}` missing links, should be `{new_text}`",
                                  line_number = line_number + card.starting_line + 1)

    def crew_entry(self, token: t.ScalarToken, key: str, text: str):
        to_replace = set()
        teams = Match.parse_partners(text.split('+')) # See Match.parse_opponents
        for team_or_member in teams:
            match team_or_member:
                case AdHocTeam() | NamedTeam() as team:
                    for m in team.members:
                        if not m.link:
                            to_replace.add(m.name)
                case NamedParticipant() as m if not m.link:
                    to_replace.add(m.name)

        to_replace.intersection_update(self.replacer.keys())

        if not to_replace:
            return

        replaced = self.replacer.replace(text, to_replace, on_match=Replacer.LINK)
        return t.ScalarToken(value=replaced, plain=token.plain, start_mark=token.start_mark, end_mark=token.end_mark)
