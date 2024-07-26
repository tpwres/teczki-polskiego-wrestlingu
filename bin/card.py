import yaml
import io
from typing import Union, Iterable, Optional, Tuple, NamedTuple, cast
import re
from pathlib import Path
from itertools import chain
from dataclasses import dataclass
from contextlib import contextmanager
import yaml.parser
from sys import exit, stderr

person_link_re = re.compile(r'''
    ^
    \[ # Square brackets surround link text
        (?: # Optional prefix
          (?P<delim>[*_]) # begins with an underscore or asterisk
          (?P<prefix>.*?) # followed by text
          (?P=delim) # ends with the same delimiter character
        )?
        \s* # May be followed by whitespace
        (?P<text>.*?)
        (?:\(c\))? # May have a champion marker, which we do not capture
        (?: # Optional suffix
          (?P<sdelim>[*_]) # begins with an underscore or asterisk
          (?P<suffix>.*?) # followed by text
          (?P=sdelim) # ends with the same delimiter character
        )?
    \]
    \( # Then, parentheses surround link target
        (?P<target>.*?)
    \)
    (?:\(c\))? # The champion marker may also be outside
    \s* # Eat whitespace
    $
''', re.VERBOSE)

person_plain_re = re.compile(r'''
    ^
    (?: # Optional part
        (?P<delim>[*_]) # begins with an underscore or asterisk
        (?P<prefix>.*?) # followed by text
        (?P=delim) # ends with the same delimiter character
    )?
    (?P<text>.*?)
    (?:\(c\))? # Optional champion marker
    (?: # Optional suffix
        (?P<sdelim>[*_]) # begins with an underscore or asterisk
        (?P<suffix>.*?) # followed by text
        (?P=sdelim) # ends with the same delimiter character
    )?
    \s* # Eat whitespace
    $
''', re.VERBOSE)

@dataclass(frozen=True)
class Name:
    name: str
    link: Optional[str] = None
    annotation: Optional[str] = None

    def __init__(self, name_or_link: str):
        if m := person_link_re.match(name_or_link):
            # __setattr__ is required boilerplate when using frozen dataclass
            object.__setattr__(self, 'name', m.group('text'))
            object.__setattr__(self, 'link', m.group('target'))
            object.__setattr__(self, 'prefix', m.group('prefix'))
            object.__setattr__(self, 'suffix', m.group('suffix'))
        elif m := person_plain_re.match(name_or_link):
            if '[' in name_or_link:
                # Capture broken markdown links
                raise ValueError(name_or_link)
            object.__setattr__(self, 'name', m.group('text').strip())
            object.__setattr__(self, 'prefix', m.group('prefix'))
            object.__setattr__(self, 'suffix', m.group('suffix'))
        else:
            raise ValueError(name_or_link)

    def __repr__(self) -> str:
        cls = self.__class__.__name__ # Important for subclasses
        return f"{cls}({self.format_link()})"

    def format_link(self):
        if self.annotation:
            return f"{{{self.annotation}}}[{self.name}]({self.link})"

        return f"[{self.name}]({self.link})"

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
    members: list

    def __init__(self, members):
        self.members = members

    def __repr__(self) -> str:
        return "{}(m={!r})".format(self.__class__.__name__, self.members)

class Fighter(NamedParticipant):
    pass

class Manager(NamedParticipant):
    pass

class CrewMember(NamedParticipant):
    def __init__(self, name_or_link: str, role: str):
        super().__init__(name_or_link)
        self.role = role

    def __repr__(self) -> str:
        repr = super().__repr__()
        return "{}:{}".format(repr, self.role)


def parse_maybe_team(text) -> Union[Participant, Team]:
    match Match.tag_team_re.match(text):
        case re.Match() as m:
            team_name = m.group('team')
            people = m.group('people')
        case _:
            team_name = None
            people = text

    group = parse_group(people)
    match (group, team_name):
        case ([single_member], _):
            return single_member
        case ([*members], None):
            return AdHocTeam(members)
        case ([*members], name):
            return NamedTeam(name, members)

def parse_group(text) -> list[Participant]:
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

class Match:
    tag_team_re = re.compile(r'''
        ^
         (?:
           (?P<team>[\w\s]+) # Team name followed by a colon
           (?:\s*\(c\))? # Optional champion marker
           : # Followed by a colon
         )? # All optional
         \s* # Eat whitespace
         (?P<people>.+) # Followed by list of participants
         \s* # Eat trailing space
        ''', re.VERBOSE)

    def __init__(self, match_row: list[str|dict], index: int):
        self.line = match_row # Store original row
        self.index = index
        match match_row:
            case [*participants, dict() as options]:
                participants = cast(list[str], participants)
                self.opponents = list(self.parse_opponents(participants))
                self.options = options
            case [*participants]:
                participants = cast(list[str], participants)
                self.opponents = list(self.parse_opponents(participants))
                self.options = {}
            case dict() as options:
                self.opponents = []
                self.options = options

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
        return [parse_maybe_team(p) for p in partners]

class Crew:
    def __init__(self, credits: dict, index: int):
        self.credits = credits
        self.index = index
        self.members = []
        for role, names in credits.items():
            self.members.extend(CrewMember(p.name, role) for p in parse_group(names) if isinstance(p, NamedParticipant))

class CardParseError(Exception):
    pass

class DelimitedCard(NamedTuple):
    start: int
    end: int
    text: str
    card_start_line: int

class Card:
    def __init__(self, text_or_io: Union[str, io.TextIOBase], path: Optional[Path]):
        match text_or_io:
            case str() as text:
                # parse_result = self.extract_card(text_or_io.split("\n"))
                extracted_card = self.extract_card_unsplit(text)
            case io.TextIOBase() as stream:
                extracted_card = self.extract_card_unsplit(stream.read())

        if extracted_card:
            card_start, card_end, card_text, _ = extracted_card
            self.start_offset = card_start
            self.end_offset = card_end
            with self.handle_yaml_errors(extracted_card, path):
                content = list(self.parse_card(card_text))

            if not content:
                raise ValueError("Failed to find valid matches")

            if isinstance(content[-1], Crew):
                self.crew = cast(Crew, content.pop())
            else:
                self.crew = None
            self.matches = cast(list[Match], content)
        else:
            self.matches = self.crew = None


    @contextmanager
    def handle_yaml_errors(self, card_block: DelimitedCard, path: Optional[Path]):
        try:
            yield
        except yaml.parser.ParserError as parse_error:
            _, _, _, start_line = card_block
            context, _, problem, problem_mark = parse_error.args
            line = start_line + problem_mark.line
            message = f"{path or '<file>'}:{line}: Error: {problem} {context}\n"
            stderr.write(message)
            raise CardParseError(message)

    def extract_card_unsplit(self, text: str) -> Optional[DelimitedCard]:
        start_pattern = '{% card() %}'
        start_length = len(start_pattern) + 1 # Accounting for the new line

        card_start = text.find(start_pattern)
        if card_start == -1:
            return None
        start_line = text[:card_start].count("\n") + 2 # 1 for line numbering to start at 1, and 1 more to consume the {% card %} block start
        card_end = text.find('{% end %}', card_start + start_length)
        body = text[card_start + start_length:card_end]

        return DelimitedCard(card_start + start_length, card_end, body, start_line)

    def parse_card(self, card_text: str) -> Iterable[Match|Crew]:
        card_rows = yaml.safe_load(io.StringIO(card_text))
        for i, row in enumerate(card_rows):
            match row:
                case {"credits": dict() as credits}:
                    yield Crew(credits, i)
                case [*_]:
                    yield Match(cast(list[str|dict], row), i)

