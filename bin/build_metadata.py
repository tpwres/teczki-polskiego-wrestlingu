#! /usr/bin/env python3

import re
from pathlib import Path
from datetime import datetime
from collections import Counter
import json
from functools import reduce

from utils import parse_front_matter, RichEncoder, accepted_name
from card import Card

def extract_names(matches):
    return reduce(lambda a, b: a | b, [set(m.all_names()) for m in matches], set([]))

# Not strictly necessary as the career hash can be used to pull the same info
def update_years_active(years, card, front_matter):
    names = extract_names(card.matches)
    event_date = front_matter['date']

    for person in names:
        if not accepted_name(person.name): continue
        years.setdefault(person.name, set()).add(event_date.year)

def update_career(career, card, front_matter):
    event_date = front_matter['date']
    orgs = front_matter['orgs']
    names = extract_names(card.matches)

    for person in names:
        plain = person.name
        if not accepted_name(plain): continue

        entry = career.setdefault(plain, {})
        year = entry.setdefault(event_date.year, Counter())
        year.update(orgs)

def main():
    years_active = {}
    career = {}
    date_org_re = re.compile(r'^\d{4}-\d{2}-\d{2}-(\w+)-')
    cwd = Path.cwd()

    events_dir = cwd / "content/e"
    # Omit _index.md pages
    event_pages = events_dir.glob("**/????-??-??-*.md")

    for page in event_pages:
        print("Loading %s" % page)
        page_date = datetime.strptime(page.stem[:10], "%Y-%m-%d").date()

        defaults = { 'date': page_date, 'org': None }
        if org_match := date_org_re.match(page.stem):
            defaults['orgs'] = org_match.group(1).split('_')

        text = page.read_text(encoding='utf-8')
        front_matter = defaults | parse_front_matter(text)
        card = Card(text)
        if not card.matches:
            print("No card available, skipping")
            continue
        update_years_active(years_active, card, front_matter)
        update_career(career, card, front_matter)

    data_dir = cwd / 'data'
    data_dir.mkdir(exist_ok=True)


    with (data_dir / 'years-active.json').open('w') as f:
        print("Saving years active to %s" % f.name)
        json.dump(years_active, f, cls=RichEncoder)

    with (data_dir / 'career.json').open('w') as f:
        print("Saving career to %s" % f.name)
        json.dump(career, f, cls=RichEncoder)


if __name__ == "__main__":
    main()
