#! /usr/bin/env python3

from pathlib import Path
import re
from utils import parse_front_matter, accepted_name
from card import Card, Fighter, Manager
import json
from collections import Counter
from functools import reduce

def main():
    org_rosters = {}
    cwd = Path.cwd()
    # 1. List all event pages
    events_dir = cwd / "content/e"
    event_pages = events_dir.glob("????-??-??-*.md")
    # 2. For each event page, determine it's organization (can be more than one) from page name or frontmatter
    org_re = re.compile(r'^[-\d]+-([^-]+)')
    for page in event_pages:
        print("Loading %s" % page)
        defaults = {}
        if org_match := org_re.match(page.stem):
            defaults['orgs'] = org_match.group(1).split('_')

        text = page.read_text(encoding='utf-8')
        front_matter = defaults | parse_front_matter(text)

        orgs = front_matter['orgs']
        # 3. Find and read the card() block
        card = Card(text)
        if not card.matches: continue

        # 4. Grab all talent names in that block
        names = [person for person in extract_names(card.matches) if accepted_name(person.name)]
        # 5. Add to a set of names for relevant orgs
        for org in orgs:
            roster = org_rosters.setdefault(org, Counter())
            roster.update(names)

    data_dir = cwd / "data"
    # 6. At the end, sanitize the set: remove duplicates where one is a md link and the other isn't, keeping the link.
    for org, roster in org_rosters.items():
        roster = sanitize_roster(roster)
        with (data_dir / "roster_{}.json".format(org)).open('w') as fp:
            json.dump(roster, fp)
    # 7. Output JSON files


def extract_names(matches):
    return reduce(lambda a, b: a | b, [set(m.all_names()) for m in matches], set([]))

def sanitize_roster(roster):
    # Roster is a Counter where keys are Name objects, but may either be ones
    # that have markdown links or not
    # Collapse so that if there are both for a single person,
    # only the markdown one remains, and its value is the sum of both entries.
    out = Counter()
    plain_map = {}

    print(list(roster.keys()))

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
