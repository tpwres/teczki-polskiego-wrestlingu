#! /usr/bin/env python3

import re
from utils import accepted_name
from card import Match, CardParseError
from page import EventPage
from pathlib import Path
from datetime import date
import json
from sys import stderr, exit

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
    num_errors = 0
    appearances = {}
    crew_appearances = {}
    all_bouts = []
    cwd = Path.cwd()
    # 1. List all event pages
    content_dir = cwd / 'content'
    events_dir = content_dir / "e"
    event_pages = events_dir.glob("**/????-??-??-*.md")
    # 2. For each event page, determine it's organization (can be more than one) from page name or frontmatter
    i = 0
    for path in event_pages:
        try:
            page = EventPage(path, verbose=False)
            card = page.card
            if not card.matches: continue
        except CardParseError:
            num_errors += 1
            continue

        relative_path = path.relative_to(content_dir).as_posix()

        for bout in card.matches:
            all_bouts.append(
                dict(
                    d=page.event_date,
                    o=page.orgs,
                    n=page.title,
                    m=bout,
                    p=relative_path
                )
            )
            for person in bout.all_names():
                if not accepted_name(person.name): continue
                bouts = appearances.setdefault(person.name, [])
                bouts.append(i)
            i += 1

        if not card.crew: continue

        for person in card.crew.members:
            if not accepted_name(person.name): continue
            events = crew_appearances.setdefault(person.name, [])
            events.append(
                dict(
                    d=page.event_date,
                    o=page.orgs,
                    n=page.title,
                    p=relative_path,
                    r=person.role
                )
            )

    if num_errors > 0:
        stderr.write("Errors found, aborting\n")
        exit(1)

    data_dir = cwd / 'data'
    data_dir.mkdir(exist_ok=True)

    with (data_dir / 'appearances.json').open('w') as f:
        print("Saving appearance map to %s" % f.name)
        json.dump(appearances, f)

    with (data_dir / 'crew_appearances.json').open('w') as f:
        print("Saving crew appearance map to %s" % f.name)
        json.dump(crew_appearances, f, cls=MatchEncoder)

    with (data_dir / 'all_matches.json').open('w') as f:
        print("Saving all matches to %s" % f.name)
        json.dump(all_bouts, f, cls=MatchEncoder)

if __name__ == "__main__":
    main()
