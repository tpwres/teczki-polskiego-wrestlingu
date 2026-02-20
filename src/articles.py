from pathlib import Path
from page import page
from typing import cast

def load_existing_name_articles() -> dict[str, Path]:
    cwd = Path.cwd()
    talent_dir = cwd / 'content/w'
    name_files = talent_dir.glob('*.md')
    names = {}
    for path in name_files:
        if path.name == '_index.md': continue
        if path.name.startswith('.'): continue

        article = page(path)
        front_matter = article.front_matter
        names[front_matter['title']] = path
        if extra := front_matter.get('extra'):
            extra = cast(dict[str, str], extra)
            for alias in extra.get('career_aliases', []):
                names[alias] = path
            if cname := extra.get('career_name', ''):
                names[cname] = path

    return names

def load_event_articles() -> dict[str, Path]:
    cwd = Path.cwd()
    events_dir = cwd / 'content/e'
    all_event_files = events_dir.glob('**/????-??-??-*.md')
    events_dict = {}
    for path in all_event_files:
        event = page(path)
        title = event.front_matter['title']

        events_dict[title] = path
    return events_dict
