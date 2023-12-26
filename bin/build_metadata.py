#! /usr/bin/env python3

import re
from pathlib import Path
from datetime import datetime
from collections import Counter
import json

from utils import parse_front_matter, RichEncoder

# Not strictly necessary as the career hash can be used to pull the same info
def update_years_active(years, data):
    if 'extra' not in data: return
    extra = data['extra']
    if 'all_talent' not in extra: return
    talent = extra['all_talent']

    event_date = data['date']

    for name in talent:
        years.setdefault(name, set()).add(event_date.year)

def update_career(career, data):
    if 'extra' not in data: return
    extra = data['extra']
    if 'all_talent' not in extra: return
    talent = extra['all_talent']

    event_date = data['date']

    org = extra.get('org', data['org'])

    # How do we reconcile multiple names for the same person?
    for name in talent:
        entry = career.setdefault(name, {})
        year = entry.setdefault(event_date.year, Counter())
        year.update([org])

def main():
    years_active = {}
    career = {}
    date_org_re = re.compile(r'^\d{4}-\d{2}-\d{2}-(\w+)-')
    cwd = Path.cwd()

    events_dir = cwd / "content/e"
    # Omit _index.md pages
    event_pages = events_dir.glob("????-??-??-*.md")

    for page in event_pages:
        print("Loading %s" % page)
        page_date = datetime.strptime(page.stem[:10], "%Y-%m-%d").date()

        defaults = { 'date': page_date, 'org': None }
        if org_match := date_org_re.match(page.stem):
            defaults['org'] = org_match.group(1)

        text = page.read_text(encoding='utf-8')
        front_matter = defaults | parse_front_matter(text)
        update_years_active(years_active, front_matter)
        update_career(career, front_matter)

    data_dir = cwd / 'data'
    data_dir.mkdir(exist_ok=True)

    with (data_dir / 'years-active.json').open('w') as f:
        print("Saving years active to %s" % f.name)
        json.dump(years_active, f, cls=RichEncoder)

    with (data_dir / 'career.json').open('w') as f:
        print("Saving career to %s" % f.name)
        json.dump(career, f, cls=RichEncoder)

    print(career)


if __name__ == "__main__":
    main()
