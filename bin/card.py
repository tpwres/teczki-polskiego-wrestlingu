import yaml
import io
from typing import Union, Iterable, Optional, Tuple
import re
from itertools import chain
from dataclasses import dataclass

markdown_link_re = re.compile(r'''
    ^
    \[ # Square brackets surround link text
        (?P<text>.*?)
        (?:\(c\))? # May have a champion marker, which we do not capture
    \]
    \( # Then, parentheses surround link target
        (?P<target>.*?)
    \)
    (?:\(c\))? # The champion marker may also be outside
    \s* # Eat whitespace
    $
''', re.VERBOSE)

@dataclass(frozen=True)
class Name:
    name: str
    link: Optional[str] = None

    def __init__(self, name_or_link: str):
        match markdown_link_re.match(name_or_link):
            case re.Match() as m:
                # __setattr__ is required boilerplate when using frozen dataclass
                object.__setattr__(self, 'name', m.group('text'))
                object.__setattr__(self, 'link', m.group('target'))
            case _:
                if '[' in name_or_link:
                    raise ValueError(name_or_link)
                object.__setattr__(self, 'name', name_or_link.strip().replace("(c)", ""))

    def __repr__(self) -> str:
        cls = self.__class__.__name__ # Important for subclasses
        return "{}({})".format(cls, self.format_link())

    def format_link(self):
        return "[{0}]({1})".format(self.name, self.link)

class Participant:
    # Abstract
    def all_names(self) -> Iterable[Name]:
        raise NotImplementedError

class NamedParticipant(Participant, Name):
    def all_names(self) -> Iterable[Name]:
        yield self

class Team(Participant):
    def all_names(self) -> Iterable[Name]:
        yield from getattr(self, 'members', [])

class NamedTeam(Team):
    def __init__(self, team_name, members):
        self.team_name = team_name
        self.members = members

    def __repr__(self) -> str:
        return "{}(n={} m={!r})".format(self.__class__.__name__, self.team_name, self.members)

class AdHocTeam(Team):
    def __init__(self, members):
        self.members = members

    def __repr__(self) -> str:
        return "{}(m={!r})".format(self.__class__.__name__, self.members)

class Fighter(NamedParticipant):
    pass

class Manager(NamedParticipant):
    pass


class Match:
    tag_team_re = re.compile(r'''
        ^(?:(?P<team>[\w\s]+):)? # An optional team name followed by a colon
         \s* # Optional space
         (?P<people>.+) # Followed by list of participants
         \s* # Eat trailing space
        ''', re.VERBOSE)

    def __init__(self, match_row: list[str], index: int):
        self.line = match_row # Store original row
        self.index = index
        match match_row:
            case [*participants, dict() as options]:
                self.opponents = list(self.parse_opponents(participants))
                self.options = options
            case [*participants]:
                self.opponents = list(self.parse_opponents(participants))
                self.options = {}

    def __repr__(self) -> str:
        return "Match(i={},o={!r} f={!r})".format(self.index, self.opponents, self.options)

    def all_names(self) -> Iterable[Name]:
        for opp in self.opponents:
            yield from chain.from_iterable(s.all_names() for s in opp)

    def winner(self) -> Iterable[Participant]:
        return self.opponents[0]

    def parse_opponents(self, opponents: list[str]) -> Iterable[Iterable[Participant]]:
        return [self.parse_partners(side.split("+")) for side in opponents]

    def parse_partners(self, partners: list[str]) -> Iterable[Participant]:
        return [self.parse_maybe_team(p) for p in partners]

    def parse_maybe_team(self, text) -> Union[Participant, Team]:
        match Match.tag_team_re.match(text):
            case re.Match() as m:
                team_name = m.group('team')
                people = m.group('people')
            case _:
                team_name = None
                people = text

        group = self.parse_group(people)
        match (group, team_name):
            case ([single_member], _):
                return single_member
            case ([*members], None):
                return AdHocTeam(members)
            case ([*members], name):
                return NamedTeam(name, members)

    def parse_group(self, text) -> list[Participant]:
        # Split with capture keeps delimiters in the result list
        tokenized = re.split(r'\s*([,;])\s*', text)
        first_name = tokenized.pop(0)
        combatants: list[Participant] = [Fighter(first_name)]

        while len(tokenized) > 0:
            match tokenized:
                case [',', name, *rest]:
                    combatants.append(Fighter(name.strip()))
                    tokenized = rest
                case [';', name, *rest]:
                    combatants.append(Manager(name.strip()))
                    tokenized = rest
                case _:
                    raise ValueError("{!r}".format(tokenized))

        return combatants

class Card:
    def __init__(self, text_or_io: Union[str, io.TextIOBase]):
        match text_or_io:
            case str() as text:
                # parse_result = self.extract_card(text_or_io.split("\n"))
                parse_result = self.extract_card_unsplit(text)
            case io.TextIOBase() as stream:
                parse_result = self.extract_card_unsplit(stream.read())

        if parse_result:
            card_start, card_end, card_text = parse_result
            self.start_offset = card_start
            self.end_offset = card_end
            self.matches = self.parse_card(card_text)
        else:
            self.matches = None

    DelimitedCard = Tuple[int, int, str]

    def extract_card_unsplit(self, text: str) -> Optional[DelimitedCard]:
        start_pattern = '{% card() %}'
        start_length = len(start_pattern) + 1 # Accounting for the new line

        card_start = text.find(start_pattern)
        if card_start == -1:
            return None
        card_end = text.find('{% end %}', card_start + start_length)
        body = text[card_start + start_length:card_end]

        return (card_start + start_length, card_end, body)

    def parse_card(self, card_text: str) -> Iterable[Match]:
        match_rows = yaml.safe_load(io.StringIO(card_text))
        return [Match(row, i) for i, row in enumerate(match_rows)]

