import datetime
import yaml
import io
from warnings import deprecated
from typing import Union, Iterable, Optional, cast, Any
import re
from pathlib import Path
from dataclasses import dataclass
from contextlib import contextmanager
import yaml.parser

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


card_start_re = re.compile(r'''
    ^
    \{%\s+
        card\(
            (?P<params>.+)? # Optional params
        \)
    \s+%\}
    $
''', re.VERBOSE | re.MULTILINE)

param_re = re.compile(r'''
    (\w+)\s*=\s* # key=, with optional spaces
    (
        (?P<delim>['\"]) # opening single or double quote, for string values
        \w+
        (?P=delim) # closing quote of the same flavor
        |\w+ # instead of a quoted value, raw keyword
    )
    (?:,\s+|$) # followed by a comma and spaces
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
                raise MatchParseError(f"Malformed participant name {name_or_link!r}")
            object.__setattr__(self, 'name', m.group('text').strip())
            object.__setattr__(self, 'prefix', m.group('prefix'))
            object.__setattr__(self, 'suffix', m.group('suffix'))
        else:
            raise MatchParseError(name_or_link)

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
    members: list

    def __init__(self, team_name, members):
        self.team_name = team_name
        self.members = members

    def __repr__(self) -> str:
        return f"NamedTeam(n={self.team_name} m={self.members!r})"

class AdHocTeam(Team):
    members: list

    def __init__(self, members):
        self.members = members

    def __repr__(self) -> str:
        return f"AdHocTeam(m={self.members!r})"

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


class Match:
    line: list
    index: int
    opponents: list[Iterable[Participant]]
    options: dict
    date: Optional[datetime.date]

    tag_team_re = re.compile(r'''
        ^
         (?:
           (?P<team>[-'\w\s]+) # Team name followed by a colon
           (?:\s*\(c\))? # Optional champion marker
           : # Followed by a colon
         )? # All optional
         \s* # Eat whitespace
         (?P<people>.+) # Followed by list of participants
         \s* # Eat trailing space
        ''', re.VERBOSE)

    def __init__(self, match_row: list[str|dict], index: int, date: Optional[datetime.date]):
        self.line = match_row # Store original row
        self.index = index
        self.date = date
        match match_row:
            case [*participants, dict() as options]:
                participants = cast(list[str], participants)
                self.opponents = list(self.parse_opponents(participants, index))
                self.options = options
            case [*participants]:
                participants = cast(list[str], participants)
                self.opponents = list(self.parse_opponents(participants, index))
                self.options = {}
            case dict() as options:
                self.opponents = []
                self.options = options

    def __repr__(self) -> str:
        return "Match(i={},o={!r} f={!r})".format(self.index, self.opponents, self.options)

    def all_names(self) -> Iterable[Name]:
        return (name
                for person_or_team in self.opponents
                for members in person_or_team
                for name in members.all_names()
                )

    def all_names_indexed(self):
        return ((i, name)
                for i, person_or_team in enumerate(self.opponents)
                for members in person_or_team
                for name in members.all_names()
                )

    def winner(self) -> Iterable[Participant]:
        return self.opponents[0]

    def parse_opponents(self, opponents: list, index: Optional[int] = None) -> Iterable[Iterable[Participant]]:
        for side in opponents:
            match side:
                case None:
                    message = f"Match {index + 1}: at least one side in match is empty" if index else "Malformed match in card: at least one side is empty"
                    raise MatchParseError(message)
                case str():
                    yield self.parse_partners(side.split("+"))
                case _:
                    message = f"Match {index + 1}: unexpected match participant {side!r}" if index else f"Unexpected match participant {side!r}"
                    raise MatchParseError(message)


    def parse_partners(self, partners: list[str]) -> Iterable[Union[Participant, Team]]:
        return [t for p in partners if (t := self.parse_maybe_team(p))]

    def parse_maybe_team(self, text: str) -> Optional[Union[Participant, Team]]:
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

tokenizer_re = re.compile(r'''
  \s* # May include leading space, especially relevant for w/ and &
    (
      [,;&] | # single-char delimiters
      (?:
        (?<!@/) # NOT preceded by @/, i.e. not part of a talent page link
        w/
      )
    )
  \s*
''', re.X)

def parse_group(text) -> list[Participant]:
    # Split with capture keeps delimiters in the result list
    tokenized = tokenizer_re.split(text)
    first_name = tokenized.pop(0)
    combatants: list[Participant] = [Fighter(first_name)]
    last_participant_type = Fighter

    while len(tokenized) > 0:
        match tokenized:
            case [',', name, *rest]:
                combatants.append(Fighter(name.strip()))
                last_participant_type = Fighter
                tokenized = rest
            case [w, name, *rest] if w in ('w/', ';'):
                combatants.append(Manager(name.strip()))
                last_participant_type = Manager
                tokenized = rest
            case ['&', name, *rest]:
                person = last_participant_type(name.strip())
                combatants.append(person)
                tokenized = rest
            case _:
                raise ValueError("{!r}".format(tokenized))

    return combatants

class Crew:
    def __init__(self, credits: dict, index: int):
        self.credits = credits
        self.index = index
        self.members = []
        for role, names in credits.items():
            self.members.extend(
                CrewMember(p.format_link() if p.link else p.name, role)
                for p in parse_group(names)
                if isinstance(p, NamedParticipant)
            )

class CardParseError(Exception):
    pass

class MatchParseError(CardParseError):
    pass

class Card:
    crew: Optional[Crew]
    matches: list[Match]
    params: dict[str, Any]

    def __init__(self, section, doc, error_sink=None):
        _line_start, _name, card_block = section
        self.sink = error_sink or doc.sink

        # NOTE: YAML errors are handled earlier, when parsing the block
        content = list(self.parse_card(card_block.raw_card))

        match content:
            case []:
                # Also if the card had errors
                self.matches, self.crew = [], None
            case [*matches, Crew() as crew]:
                self.matches, self.crew = cast(list[Match], matches), crew
            case [*matches]:
                self.matches, self.crew = cast(list[Match], matches), None

        self.params = self.parse_card_params(card_block.params)


    def parse_card(self, card_rows: list[Any]) -> Iterable[Match|Crew]:
        match_date = None
        for i, row in enumerate(card_rows):
            match row:
                case {"credits": dict() as credits}:
                    yield Crew(credits, i)
                case {"date": datetime.date() as new_date}:
                    match_date = new_date
                case [*_]:
                    yield Match(cast(Any, row), i, date=match_date)

    def parse_card_params(self, params: str) -> dict:
        result = {}
        for mm in param_re.finditer(params):
            key, value = mm.group(1), mm.group(2)
            match value.strip():
                case 'true' | 'True':
                    result[key] = True
                case 'false' | 'False':
                    result[key] = False
                case str() as text if text[0] == text[-1] == "'":
                    result[key] = text[1:-1]
                case str() as text if text[0] == text[-1] == '"':
                    result[key] = text[1:-1]
                case str() as num if num.isnumeric():
                    result[key] = int(num)
                case _:
                    raise CardParseError(f"Card block header: unsupported value {value}")
        return result

def extract_names(matches: Iterable[Match]) -> set[Name]:
    """
    Return a set of all distinct participants given a list of Matches.
    Match object may have an `x` key in their options. This must be a list of integer 1-based indices.
    If present, the indices mark people to REMOVE from this participant list.
    """
    names = set()
    for i, mm in enumerate(matches):
        try:
            names |= names_in_match(mm)
        except MatchParseError as mpe:
            # This is the "Unexpected participant" message. Prefix it with the match number.
            message, = mpe.args
            raise MatchParseError(f"(Match {i + 1}) {message}")

    return names

def names_in_match(mm: Match) -> set[Name]:
    names: list[Optional[Name]] = list(mm.all_names())
    exclude = set(mm.options.get('x', []))

    return set(name
               for i, name in enumerate(names)
               if i + 1 not in exclude # exclude is 1-based
               and name) # Otherwise the type is set[Name|None]
