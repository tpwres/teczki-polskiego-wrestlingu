#! /usr/bin/env python3

from collections import namedtuple
from pathlib import Path
from typing import Any, Callable, Iterable, cast
from page import page, TalentPage
from unidecode import unidecode
import json, re, yaml

ATRecord = namedtuple('ATRecord', ['sort_key', 'name', 'kind', 'path', 'country', 'flag_or_emoji'])

LookupFlagFn = Callable[[str|TalentPage], tuple[str, str]]
MakeKeyFn = Callable[[str], str]

def main():
    content_path = Path.cwd() / 'content'

    careers = json.load(Path('data/career.json').open())
    name_to_flag = yaml.safe_load(Path('const/name-to-flag.yaml').open())
    flags = json.load(Path('const/flags-by-code.json').open())
    emojis = yaml.safe_load(Path('const/emojis.yaml').open())
    alias_map = json.load(Path('data/aliases.json').open())

    lookup_flag = lambda name_or_page: lookup_flag_or_emoji(name_or_page, name_to_flag, flags, emojis)

    every_talent_name = set(careers.keys()) | set(alias_map.keys())

    all_names = set()
    sort_key = lambda text: unidecode(make_sort_key(text))
    for name in every_talent_name:
        path = alias_map.get(name)

        if path:
            talent_page = TalentPage(content_path / path, verbose=False)
            other_names = [alias for alias, talent_path in alias_map.items() if talent_path == path and alias != name]
            all_names |= set(load_talent(talent_page, path, lookup_flag, make_key=sort_key, other_names=other_names))
        else:
            all_names.add(unlinked_entry(name, lookup_flag, make_key=sort_key))

    out = list(all_names)
    out.sort(key=lambda record: record.sort_key)

    save_as_json(out, Path('data/all_time_roster.json'))

def load_talent(talent_page: TalentPage, path: str, lookup_flag: LookupFlagFn, make_key: MakeKeyFn, other_names: Iterable[str]) -> Iterable[ATRecord]:
    fm = talent_page.front_matter
    title = cast(str, fm['title'])
    country, flag = lookup_flag(talent_page)

    yield ATRecord(make_key(title), title, 'P', path, country, flag)

    for other_name in other_names:
        if other_name == title: continue
        yield ATRecord(make_key(other_name), other_name, 'A', path, country, flag)

def unlinked_entry(name, lookup_flag: LookupFlagFn, make_key: MakeKeyFn) -> ATRecord:
    country, flag = lookup_flag(name)
    return ATRecord(make_key(name), name, 'U', None, country, flag)

def lookup_flag_or_emoji(name_or_page, names_dict, flags_list, emojis) -> tuple[str, str]:
    match name_or_page:
        case str() as name:
            code = names_dict.get(name)
            if not code: return 'ZZ', ''
            if code in flags_list:
                return code, flags_list[code]
            elif code in emojis:
                return code, emojis[code]
            return 'ZZ', ''
        case TalentPage(front_matter=fm):
            taxonomies = cast(dict[str, Any], fm.get('taxonomies', {}))
            code = taxonomies.get('country', [])[0]
            if not code: return code, ''
            if code in flags_list:
                return code, flags_list[code]
            elif code in emojis:
                return code, emojis[code]
            return 'ZZ', ''
        case _:
            return 'ZZ', ''

def make_sort_key(text):
    text = re.sub(r'^The\s+', '', text)
    text = re.sub(r'\W+', '-', text)
    return text.strip('-').lower()

def save_as_json(data: Any, path: Path):
    with path.open('w') as fp:
        json.dump(data, fp)

if __name__ == "__main__":
    main()
