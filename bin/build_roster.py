#! /usr/bin/env python3

from pathlib import Path
from utils import accepted_name
import json
from collections import Counter
from functools import reduce
from card import Match, Name
from page import Page
from typing import Optional

def main():
    org_rosters = {}
    cwd = Path.cwd()
    # 1. List all event pages
    events_dir = cwd / "content/e"
    event_pages = events_dir.glob("**/????-??-??-*.md")
    # 2. For each event page, determine it's organization (can be more than one) from page name or frontmatter
    for path in event_pages:
        page = Page(path)

        # 3. Find and read the card() block
        card = page.card
        if not card.matches: continue

        # 4. Grab all talent names in that block
        names = [person for person in extract_names(card.matches) if accepted_name(person.name)]
        # 5. Add to a set of names for relevant orgs
        for org in page.orgs:
            roster = org_rosters.setdefault(org, Counter())
            roster.update(names)

    data_dir = cwd / "data"
    data_dir.mkdir(exist_ok=True)
    # 6. At the end, sanitize the set: remove duplicates where one is a md link and the other isn't, keeping the link.
    for org, roster in org_rosters.items():
        roster = sanitize_roster(roster)
        with (data_dir / "roster_{}.json".format(org)).open('w') as fp:
            json.dump(roster, fp)
    # 7. Output JSON files


def extract_names(matches: list[Match]) -> set[Name]:
    # Same as in build_metadata.py
    initial: set[Name] = set([])
    for m in matches:
        names: list[Optional[Name]] = list(m.all_names())
        exclude = m.options.get('x', [])
        for exclude_index in exclude:
            names[exclude_index - 1] = None
        for name in names:
            if name is None: continue
            initial.add(name)
    return initial

def sanitize_roster(roster):
    # Roster is a Counter where keys are Name objects, but may either be ones
    # that have markdown links or not
    # Collapse so that if there are both for a single person,
    # only the markdown one remains, and its value is the sum of both entries.
    out = Counter()
    plain_map = {}

    for person in roster.keys():
        if person.link:
            md_link = person.format_link()
            plain_map[person.name] = md_link
            out[md_link] += roster[person]

    for plain, link in plain_map.items():
        out[link] += roster[plain]

    for person in roster.keys():
        if person.name in plain_map: continue
        if person.link: continue

        out[person.name] += roster[person]

    return out

if __name__ == "__main__":
    main()
