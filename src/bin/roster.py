#! /usr/bin/env python3

from pathlib import Path
from utils import accepted_name
import json
from collections import Counter
from functools import reduce
from card import extract_names
from page import all_event_pages
from sys import stderr, exit
from sink import ConsoleSink

def main():
    org_rosters = {}
    cwd = Path.cwd()
    sink = ConsoleSink()
    for page in all_event_pages(sink=sink):
        card = page.card
        if not (card and card.matches):
            continue

        names = [person for person in extract_names(card.matches) if accepted_name(person.name)]
        for org in page.orgs:
            roster = org_rosters.setdefault(org, Counter())
            roster.update(names)

    if not sink.empty:
        # No need to dump, ConsoleSink will do that as errors are added
        # sink.dump(stderr)
        # Exit without writing anything if errors found
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
