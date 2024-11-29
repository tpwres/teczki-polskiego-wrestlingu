
#! /usr/bin/env python3

from page import all_talent_pages
from typing import cast, Any
from pathlib import Path
import json

def main():
    content_root = Path.cwd() / 'content'
    aliases = {}

    for page in all_talent_pages():
        path = str(page.path.relative_to(content_root))
        fm = page.front_matter
        extra = cast(dict[str, Any], fm.get('extra', {}))

        title = fm['title']
        career_name = extra.get('career_name')
        career_aliases = extra.get('career_aliases', [])

        aliases[title] = path
        if career_name:
            aliases[career_name] = path
        aliases |= {ca: path for ca in career_aliases}

    save_as_json(aliases, Path('data/aliases.json'))

def save_as_json(data: Any, path: Path):
    with path.open('w') as fp:
        json.dump(data, fp)

if __name__ == "__main__":
    main()
