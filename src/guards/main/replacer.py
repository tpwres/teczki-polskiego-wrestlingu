from pathlib import Path
import json
import re
from typing import Callable, Iterable
from parse import blocks, parser as rbparser

OnMatchFn = Callable[[str], str]

class Replacer:
    LINK = 'make_internal_link'
    SUB = 'substitute'

    dictionary: dict[str, str]

    def __init__(self):
        self.dictionary = {}

    def empty(self):
        return len(self.dictionary) == 0

    def keys(self) -> Iterable[str]:
        return self.dictionary.keys()

    def with_championship_links(self):
        for championship_path in Path('content/c').rglob('*.md'):
            if championship_path.stem == '_index':
                continue
            doc = rbparser.RichDocParser().parse_file(championship_path)
            if not doc:
                continue

            championship = doc.front_matter['title']
            cpath = championship_path.relative_to('content').as_posix()
            self.dictionary[championship] = cpath

        return self

    def with_team_links(self):
        for team_path in Path('content/tt').rglob('*.md'):
            if team_path.stem == '_index':
                continue
            doc = rbparser.RichDocParser().parse_file(team_path)
            if not doc:
                continue

            team = doc.front_matter['title']
            tpath = team_path.relative_to('content').as_posix()
            self.dictionary[team] = tpath

        return self

    def with_talent_names_from_metadata(self):
        metadata_path = Path('data/aliases.json')
        if metadata_path.exists():
            self.dictionary.update(json.loads(metadata_path.read_text()))

        return self

    def replace(self, text: str, terms: Iterable[str], on_match: str|OnMatchFn = 'substitute') -> str:
        match on_match:
            case str():
                on_match_fn = getattr(self, on_match)
            case func if callable(func):
                on_match_fn = func
            case _:
                raise ValueError(f"Invalid on_match {on_match}")

        rx = re.compile('|'.join(re.escape(key) for key in terms))
        new_text = rx.sub(lambda m: on_match_fn(m.group(0)), text)

        return new_text

    def substitute(self, key: str) -> str:
        return self.dictionary[key]

    def make_internal_link(self, key: str) -> str:
        if key in self.dictionary:
            target = self.dictionary[key]
            return f"[{key}](@/{target})"
        else:
            return key
