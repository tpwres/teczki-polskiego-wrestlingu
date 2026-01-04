import datetime
import yaml
import io
from typing import Union, Iterable, Optional, NamedTuple, assert_never, cast, TextIO, Any
import re
from pathlib import Path, PurePath
from itertools import chain
from functools import reduce
from dataclasses import dataclass
from contextlib import contextmanager
import yaml.parser
from sys import exit, stderr

prefix_re = r'''
    (?P<delim>[*_]) # begins with an underscore or asterisk
    (?P<prefix>.*?) # followed by text
    (?P=delim) # ends with the same delimiter character
'''

suffix_re = r'''
    (?P<sdelim>[*_]) # begins with an underscore or asterisk
    (?P<suffix>.*?) # followed by text
    (?P=sdelim) # ends with the same delimiter character
'''

champion_marker = r'(?:\(c\))'

link_label_re = rf'''
    (?:{prefix_re})? # Optional prefix
    \s* # May be followed by whitespace
    (?P<text>.*?)
    {champion_marker}? # May have a champion marker, which we do not capture
    (?:{suffix_re})? # Optional suffix
'''

person_link_re = re.compile(rf'''
    ^\s*
    \[{link_label_re}\] # Square brackets surround link text
    \((?P<target>.*?)\) # Then, parentheses surround link target
    (?:\(c\))? # The champion marker may also be outside
    \s* # Eat whitespace
    $
''', re.VERBOSE)

person_plain_re = re.compile(rf'''
    ^
    (?:{prefix_re})? # Optional prefix
    (?P<text>.*?)
    {champion_marker}? # Optional champion marker
    (?:{suffix_re})? # Optional suffix
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

    def canonicalize(self):
        if self.link:
            link = PurePath(self.link)
            return link.stem
        else:
            return self.name.strip().lower().replace(' ', '-')

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

    def build_keys(self) -> Iterable[str]:
        raise NotImplementedError

class NamedTeam(Team):
    members: list
    # TODO: Parse link
    link: Optional[str] = None

    def __init__(self, team_name, members, link=None):
        self.team_name = team_name.strip()
        self.members = members
        self.link = link

    def __repr__(self) -> str:
        return f"NamedTeam(n={self.team_name} m={self.members!r} l={self.link})"

    def build_keys(self):
        # Named teams are identified by name or link.
        keys = [self.team_name]
        if self.link:
            keys.insert(0, self.link)

        return keys

class AdHocTeam(Team):
    members: list

    def __init__(self, members):
        self.members = members

    def __repr__(self) -> str:
        return f"AdHocTeam(m={self.members!r})"

    def build_keys(self):
        key = '&'.join(sorted(m.canonicalize() for m in self.members))
        return [key]

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

    def all_teams_indexed(self):
        return ((i, person_or_team)
                for i, opponents in enumerate(self.opponents)
                for person_or_team in opponents
                if isinstance(person_or_team, Team))

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


    @classmethod
    def parse_partners(cls, partners: list[str]) -> Iterable[Union[Participant, Team]]:
        return [t for p in partners if (t := cls.parse_maybe_team(p))]

    plain_name_re = r"[-.'&\w\s]+"
    team_link_re = rf'''
        \[(?P<label>{plain_name_re})\] # Square brackets surround link text
        \((?P<target>.*?)\) # Then, parentheses surround link target
        (?:\(c\))? # The champion marker
    '''

    team_name_re = rf'(?P<link>{team_link_re})|(?P<plain>{plain_name_re})'

    tag_team_re = re.compile(rf'''
        ^
         (?P<team>
           (?:{team_name_re}) # Team name or a link
           (?:\s*\(c\))? # Optional champion marker
           : # Followed by a colon
         )? # All optional
         \s* # Eat whitespace
         (?P<people>.+) # Followed by list of participants
         \s* # Eat trailing space
        ''', re.VERBOSE|re.DOTALL) # NOTE: Dotall makes the dot in <people> regex match newlines

    @classmethod
    def parse_maybe_team(cls, text: str) -> Optional[Union[Participant, Team]]:
        m = cls.tag_team_re.match(text)
        if not m:
            raise ValueError(f"Couldn't match {text}")

        fields = m.groupdict()
        match fields:
            case {'team': None}:
                team_name = None
                people = text
            case {'label': str() as label, 'target': str() as target, 'people': str() as match_people}:
                team_name = (label, target)
                people = match_people
            case {'plain': str() as label, 'people': str() as match_people}:
                team_name = (label, None)
                people = match_people
            case _:
                raise ValueError(f"Invalid fields {fields}")

        group = parse_group(people)
        match (group, team_name):
            case ([single_member], _):
                return single_member
            case ([*members], None):
                return AdHocTeam(members)
            case ([*members], (str() as name, str() as link)):
                return NamedTeam(name, members, link=link)
            case ([*members], (str() as name, None)):
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

class DelimitedCard(NamedTuple):
    start: int
    end: int
    text: str
    card_start_line: int
    frontmatter_offset: int
    params: dict[str, Any]

class Card:
    start_offset: Optional[int]
    end_offset: Optional[int]
    crew: Optional[Crew]
    matches: list[Match]
    params: dict[str, Any]

    def __init__(self, text_or_io: object, path: Optional[Path], offset: int):
        match text_or_io:
            case str() as text:
                # parse_result = self.extract_card(text_or_io.split("\n"))
                extracted_card = self.extract_card_unsplit(text, offset)
            case io.TextIOBase() as stream:
                extracted_card = self.extract_card_unsplit(stream.read(), offset)
            case _:
                extracted_card = None

        if not extracted_card:
            self.matches = []
            self.crew = None
            return

        card_start, card_end, card_text, _start_line, _fm_offset, params = extracted_card
        self.start_offset = card_start
        self.end_offset = card_end
        self.params = params

        with self.handle_yaml_errors(extracted_card, path):
            content = list(self.parse_card(card_text))

        if not content:
            raise ValueError("Failed to find valid matches")

        if isinstance(content[-1], Crew):
            self.crew = cast(Crew, content.pop())
        else:
            self.crew = None
        self.matches = cast(list[Match], content)


    @contextmanager
    def handle_yaml_errors(self, card_block: DelimitedCard, path: Optional[Path]):
        _, _, _, start_line, offset, _ = card_block
        try:
            yield
        except MatchParseError as mpe:
            # Add filename to messages
            message, = mpe.args # Args is a tuple
            raise MatchParseError(f"{path or '<file>'}: Error: {message}")
        except yaml.parser.ParserError as parse_error:
            context, _, problem, problem_mark = parse_error.args
            # Calculate actual line number
            # Block content starts at start_line + 1
            # problem_mark.line treats that as line 1
            # And the card is extracted from a file with frontmatter already removed,
            # so we also need to add in the frontmatter length
            line = (start_line + 1) + problem_mark.line + offset
            message = f"{path or '<file>'}:{line}: Error: {problem} {context}\n"
            # stderr.write(message)
            raise CardParseError(message)

    def extract_card_unsplit(self, text: str, frontmatter_offset: int) -> Optional[DelimitedCard]:
        card_start_match = card_start_re.search(text)
        if not card_start_match:
            return None
        card_start = card_start_match.start()
        card_params = self.parse_card_params(card_start_match.group('params'))
        start_line = text[:card_start].count("\n") + 2 # 1 for line numbering to start at 1, and 1 more to consume the {% card %} block start
        card_end = text.find('{% end %}', card_start_match.end())
        if card_end == -1:
            raise ValueError("Could not find card end marker {% end %}")
        body = text[card_start_match.end():card_end]

        return DelimitedCard(
            start=card_start_match.end(),
            end=card_end,
            text=body,
            card_start_line=start_line,
            frontmatter_offset=frontmatter_offset,
            params=card_params
        )

    def parse_card(self, card_text: str) -> Iterable[Match|Crew]:
        card_rows = yaml.safe_load(io.StringIO(card_text))
        match_date = None
        for i, row in enumerate(card_rows):
            match row:
                case {"credits": dict() as credits}:
                    yield Crew(credits, i)
                case {"date": str as new_date}:
                    match_date = new_date
                case [*_]:
                    yield Match(cast(Any, row), i, date=match_date)

    def parse_card_params(self, params: str) -> dict:
        if not params: return {}
        key, _eq, value = params.partition('=')
        match value.strip():
            case 'true' | 'True':
                return {key: True}
            case 'false' | 'False':
                return {key: False}
            case _:
                raise CardParseError(f"Card block header: unsupported value {value}")

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

def teams_in_match(mm: Match) -> set[Team]:
    team_names = [entry
                  for opponent in mm.opponents
                  for entry in opponent
                  if isinstance(entry, Team)]

    # NOTE: do we need exclude here?
    return set(team_names)
