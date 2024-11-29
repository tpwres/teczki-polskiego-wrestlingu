#! /usr/bin/env python3

from collections import namedtuple
from pathlib import Path
from typing import Any, Callable, Iterable, cast
from page import page, TalentPage
import json, re, yaml

ATRecord = namedtuple('ATRecord', ['sort_key', 'name', 'kind', 'path', 'country', 'flag_or_emoji'])

LookupFlagFn = Callable[[str|TalentPage], tuple[str, str]]

def main():
    content_path = Path.cwd() / 'content'

    careers = json.load(Path('data/career.json').open())
    name_to_flag = yaml.safe_load(Path('const/name-to-flag.yaml').open())
    flags = json.load(Path('const/flags-by-code.json').open())
    emojis = yaml.safe_load(Path('const/emojis.yaml').open())
    alias_map = json.load(Path('data/aliases.json').open())

    lookup_flag = lambda name_or_page: lookup_flag_or_emoji(name_or_page, name_to_flag, flags, emojis)

    all_names = []
    for name in careers:
        path = alias_map.get(name)

        if path:
            talent_page = TalentPage(content_path / path, verbose=False)
            all_names.extend(load_talent(talent_page, path, lookup_flag))
        else:
            all_names.append(unlinked_entry(name, lookup_flag))

    all_names.sort(key=lambda atr: atr.sort_key)
    save_as_json(all_names, Path('data/all_time_roster.json'))

def load_talent(talent_page: TalentPage, path: str, lookup_flag: LookupFlagFn) -> Iterable[ATRecord]:
    fm = talent_page.front_matter
    title = fm['title']
    country, flag = lookup_flag(talent_page)

    yield ATRecord(make_sort_key(title), title, 'P', path, country, flag)

    extra = cast(dict[str, Any], fm.get('extra', {}))
    career_name = extra.get('career_name')
    if career_name:
        yield ATRecord(make_sort_key(career_name), career_name, 'T', path, country, flag)

    aliases = cast(list[str], extra.get('career_aliases', []))
    for alias in aliases:
        yield ATRecord(make_sort_key(alias), alias, 'A', path, country, flag)

def unlinked_entry(name, lookup_flag: LookupFlagFn) -> ATRecord:
    country, flag = lookup_flag(name)
    return ATRecord(make_sort_key(name), name, 'U', None, country, flag)

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
