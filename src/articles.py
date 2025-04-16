from pathlib import Path
from page import all_talent_pages, all_event_pages
from typing import cast

def load_existing_name_articles() -> dict[str, Path]:
    cwd = Path.cwd()
    talent_dir = cwd / 'content/w'
    names = {}
    for article in all_talent_pages():
        path = article.path
        front_matter = article.front_matter
        names[front_matter['title']] = path
        if extra := front_matter.get('extra'):
            extra = cast(dict[str, str], extra)
            for alias in extra.get('career_aliases', []):
                names[alias] = path
            if cname := extra.get('career_name', ''):
                names[cname] = path

    return names

def load_names_with_aliases() -> dict[str, set[str]]:
    names = {}
    for talent in all_talent_pages():
        if talent.path.stem == '_index':
            continue

        match talent.front_matter:
            case {"extra": dict(extra), "title": str(title)}:
                preferred_name = extra.get('career_name', title)
                names[preferred_name] = set([])
                aliases = extra.get('career_aliases', [])
                names[preferred_name] |= set(cast(list[str], aliases))

    return names

def load_event_articles() -> dict[str, Path]:
    events_dict = {}
    for event in all_event_pages():
        title = event.front_matter['title']

        events_dict[title] = event.path
    return events_dict
