#! /usr/bin/env python3

from collections import namedtuple
from pathlib import Path
from typing import Any, Callable, Iterable, cast
from page import page, TalentPage
from sorting import assume_locale
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

    all_names = []
    with assume_locale('pl_PL.UTF-8') as locale:
        sort_key = lambda text: locale.strxfrm(make_sort_key(text))
        for name in careers:
            path = alias_map.get(name)

            if path:
                talent_page = TalentPage(content_path / path, verbose=False)
                all_names.extend(load_talent(talent_page, path, lookup_flag, make_key=sort_key))
            else:
                all_names.append(unlinked_entry(name, lookup_flag, make_key=sort_key))

        all_names.sort(key=lambda record: record.sort_key)

    save_as_json(all_names, Path('data/all_time_roster.json'))

def load_talent(talent_page: TalentPage, path: str, lookup_flag: LookupFlagFn, make_key: MakeKeyFn) -> Iterable[ATRecord]:
    fm = talent_page.front_matter
    title = cast(str, fm['title'])
    country, flag = lookup_flag(talent_page)

    yield ATRecord(make_key(title), title, 'P', path, country, flag)

    extra = cast(dict[str, Any], fm.get('extra', {}))
    career_name = extra.get('career_name')
    if career_name:
        yield ATRecord(make_key(career_name), career_name, 'T', path, country, flag)

    aliases = cast(list[str], extra.get('career_aliases', []))
    for alias in aliases:
        yield ATRecord(make_key(alias), alias, 'A', path, country, flag)

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
