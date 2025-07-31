from pathlib import Path
from yaml import tokens as t
import json
import re

from guards.main.base import Base
from guards.main.state_machine import CardStateMachine
from parse import blocks
from card import AdHocTeam, Match, NamedTeam, Team, NamedParticipant

class UnlinkedParticipants(Base):
    @classmethod
    def accept_path(cls, path: Path):
        is_event_article = path.is_relative_to('content/e') and path.stem != '_index'

        return is_event_article

    def __init__(self):
        super().__init__()
        self.names = self.load_names_from_metadata()

    def load_names_from_metadata(self):
        path = Path('data/aliases.json')
        if not path.exists(): return [] # TODO: And log a warning? Need to ensure it's logged exactly once, not once per file
        with path.open('rb') as fp:
            return json.load(fp)

    def validate_card_ast(self, ast: list[t.Token], card: blocks.CardBlock):
        # If we don't have a names dict, exit immediately
        if not self.names:
            return

        replacements = []
        sm = CardStateMachine(ast, match_opponent=self.opponent)
        for token, replacement in sm:
            if replacement:
                replacements.append((token, replacement))

        # Now, replacements is a pair of tuples of (orig, replacement)
        # From orig we can grab line number, and from replacement the suggested text
        # For autocorrect, a similar process applies but if there's no replacement
        # then we collect the original token. Then a yaml emitter can reconstitute the entire document.
        for orig, repl in replacements:
            line_number = orig.start_mark.line
            old_name = orig.value
            new_name = repl.value
            # TODO: Handle the case when more than one name should be replaced - change text?
            # TODO: Can we emit a suggested diff here?
            self.logger.log_error(f"Participant `{old_name}` should be linked as `{new_name}`",
                                  line_number = line_number + card.starting_line + 1)

    def replacement_link(self, member):
        if member.link or member.name not in self.names:
            return {}

        link = self.names[member.name]
        return {member.name: f"[{member.name}](@/{link})"}

    def opponent(self, token: t.ScalarToken, text: str):
        # Split text as if a single team.
        # For each name in the team that is a plain name, look it up in our table
        # If we have a link for it, complain and return one or more replacement tokens
        to_replace = {}
        teams = Match.parse_partners(text.split('+')) # See Match.parse_opponents
        for team_or_member in teams:
            match team_or_member:
                case AdHocTeam() | NamedTeam() as team:
                    for m in team.members:
                        to_replace.update(self.replacement_link(m))
                case NamedParticipant() as m:
                    to_replace.update(self.replacement_link(m))

        if not to_replace:
            return # Nothing to do

        # Now replace all names with links at once.
        rx = re.compile('|'.join(re.escape(key) for key in to_replace))
        new_text = rx.sub(lambda m: to_replace[m.group(0)], text)

        return t.ScalarToken(value=new_text, plain=token.plain, start_mark=token.start_mark, end_mark=token.end_mark)
