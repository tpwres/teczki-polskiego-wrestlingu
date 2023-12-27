#! /usr/bin/env python3

from pathlib import Path
import re
from utils import parse_front_matter, parse_card_block
import json
from collections import Counter

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
        card = parse_card_block(text)
        if not card: continue

        # 4. Grab all talent names in that block
        names = extract_names(card)
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

def extract_names(card):
    # Card is a list of lists
    # The inner lists name participants, and the last element may be a hash of extra data, which we skip
    all_names = []
    for row in card:
        entries = row[:]
        if isinstance(entries[-1], dict):
            entries.pop()
        for entry in entries:
            all_names.extend(find_names(entry))
    return all_names

# An entry may contain more than one name
# Either as plain names, [Linked Names](@/w/someone.md)
# or Tag Team Name: ...names
# Names are separated by plus (+) signs
def find_names(entry):
    tag_team_re = re.compile('^(?:([\w\s]+):)?\s*(.+)$')
    partners = [n.strip() for n in entry.split("+")]
    all_names = []
    for maybe_team in partners:
        m = tag_team_re.match(maybe_team)
        names = re.split(r'\s*,\s*', m.group(2))
        all_names.extend(names)
    return all_names

def sanitize_roster(roster):
    # Roster is a Counter where keys may be either markdown links or plain names.
    # Collapse so that if there are both for a single person,
    # only the markdown one remains, and its value is the sum of both entries.
    # NOTE: The argument is destructively modified
    markdown_link_re = re.compile(r'^\[(.*)(?:\(c\))?\]\(.*\)$')
    link_names = [name for name in roster.keys() if markdown_link_re.match(name)]
    out = {}
    for linked_name in link_names:
        # TODO: Consider also collapsing entries based on link target
        plain_name = markdown_link_re.match(linked_name).group(1)
        out[linked_name] = roster[linked_name] + roster.get(plain_name, 0)
        del roster[plain_name]
        del roster[linked_name]

    # Strip (c) champion marker from plain names
    keys = [k for k in roster.keys() if "(c)" in k]
    for champ_name in keys:
        plain_name = champ_name.replace("(c)", "").strip()
        roster[plain_name] += roster[champ_name]
        del roster[champ_name]

    return roster | out



if __name__ == "__main__":
    main()
