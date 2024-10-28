#! /usr/bin/env python3

from pathlib import Path
from utils import accepted_name
import json
from collections import Counter
from functools import reduce
from card import CardParseError, MatchParseError, extract_names
from page import EventPage
from sys import stderr, exit

def main():
    errors = []
    org_rosters = {}
    cwd = Path.cwd()
    # 1. List all event pages
    events_dir = cwd / "content/e"
    event_pages = events_dir.glob("**/????-??-??-*.md")
    # 2. For each event page, determine it's organization (can be more than one) from page name or frontmatter
    for page_path in event_pages:
        try:
            page = EventPage(page_path, verbose=False)

            # 3. Find and read the card() block
            card = page.card
            if not card.matches: continue

            # 4. Grab all talent names in that block
            names = [person for person in extract_names(card.matches) if accepted_name(person.name)]
            # 5. Add to a set of names for relevant orgs
            for org in page.orgs:
                roster = org_rosters.setdefault(org, Counter())
                roster.update(names)
        except MatchParseError as mpe:
            errors.append(with_path_info(mpe, path=page_path))
        except CardParseError as e:
            errors.append(e)

    # Exit without writing anything if errors found
    if len(errors) > 0:
        for err in errors:
            print(err)
        stderr.write("Errors found, aborting\n")
        exit(1)

    data_dir = cwd / "data"
    data_dir.mkdir(exist_ok=True)
    # 6. At the end, sanitize the set: remove duplicates where one is a md link and the other isn't, keeping the link.
    for org, roster in org_rosters.items():
        roster = sanitize_roster(roster)
        # 7. Output JSON files
        with (data_dir / f"roster_{org}.json").open('w') as fp:
            json.dump(roster, fp)

def with_path_info(err: Exception, path):
    # Ideally, detect if message already has a path.
    # For now, just inject it unconditionally
    cls = err.__class__
    message, *args = err.args
    return cls(f"{path}: {message}", *args)

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
