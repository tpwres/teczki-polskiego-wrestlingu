#! /usr/bin/env python3

import re
from utils import parse_front_matter
from card import Card, Match
from pathlib import Path
from dataclasses import dataclass
from datetime import datetime, date
import json

class MatchEncoder(json.JSONEncoder):
    def default(self, obj):
        match obj:
            case Match():
                return obj.line
            case date():
                return obj.strftime("%Y-%m-%d")
            case _:
                return super().default(obj)

def main():
    appearances = {}
    all_bouts = []
    cwd = Path.cwd()
    # 1. List all event pages
    content_dir = cwd / 'content'
    events_dir = content_dir / "e"
    event_pages = events_dir.glob("????-??-??-*.md")
    # 2. For each event page, determine it's organization (can be more than one) from page name or frontmatter
    date_org_re = re.compile(r'^(?P<date>\d{4}-\d\d-\d\d)-(?P<orgs>[^-]+)')
    i = 0
    for page in event_pages:
        print("Loading %s" % page)
        defaults = {}
        if m := date_org_re.match(page.stem):
            defaults['orgs'] = m.group('orgs').split('_')
            defaults['date'] = datetime.strptime(m.group('date'), '%Y-%m-%d').date()

        text = page.read_text(encoding='utf-8')
        front_matter = defaults | parse_front_matter(text)

        orgs = front_matter['orgs']
        event_date = front_matter['date']
        event_name = front_matter['title']

        # 3. Find and read the card() block
        card = Card(text)
        if not card.matches: continue

        for bout in card.matches:
            all_bouts.append(
                dict(
                    d=event_date,
                    o=orgs,
                    n=event_name,
                    m=bout,
                    p=page.relative_to(content_dir).as_posix()
                )
            )
            for person in bout.all_names():
                bouts = appearances.setdefault(person.name, [])
                bouts.append(i)
            i += 1

    data_dir = cwd / 'data'
    data_dir.mkdir(exist_ok=True)

    with (data_dir / 'appearances.json').open('w') as f:
        print("Saving appearance map to %s" % f.name)
        json.dump(appearances, f)

    with (data_dir / 'all_matches.json').open('w') as f:
        print("Saving all matches to %s" % f.name)
        json.dump(all_bouts, f, cls=MatchEncoder)

if __name__ == "__main__":
    main()
