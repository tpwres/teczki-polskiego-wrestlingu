#! /usr/bin/env python3

from pathlib import Path
from collections import Counter
from articles import load_names_with_aliases
import json
from functools import reduce
from typing import Iterable, cast, Optional
from utils import RichEncoder, accepted_name
from card import Match, Name
from page import Page

def extract_names(matches: Iterable[Match]) -> set[Name]:
    """
    Return a set of all distinct participants given a list of Matches.
    Match object may have an `x` key in their options. This must be a list of integer 1-based indices.
    If present, the indices mark people to REMOVE from this participant list.
    """
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

# Not strictly necessary as the career hash can be used to pull the same info
def update_years_active(years: dict[str, set[int]], page: Page):
    if not page.card.matches: return
    if not page.event_date: return

    names = extract_names(page.card.matches)

    for person in names:
        if not accepted_name(person.name): continue
        years.setdefault(person.name, set()).add(page.event_date.year)

OrgYears = dict[str, int]
CareerYears = dict[int, OrgYears]

def update_career(career: dict[str, CareerYears], page: Page):
    event_date = page.event_date
    orgs = page.orgs
    card = page.card

    if not card.matches:
        return

    if not event_date:
        return

    names = extract_names(card.matches)

    for person in names:
        plain = person.name
        if not accepted_name(plain): continue

        entry = career.setdefault(plain, {})
        year = cast(Counter, entry.setdefault(event_date.year, Counter()))
        year.update(orgs)

    if not card.crew: return
    for person in card.crew.members:
        entry = career.setdefault(person.name, {})
        year = cast(Counter, entry.setdefault(event_date.year, Counter()))
        year.update(orgs)

def merge_years(left: CareerYears, right: CareerYears) -> CareerYears:
    result = left.copy()
    for key in right:
        year = result.setdefault(key, Counter())
        year.update(right[key])

    return result

def merge_aliases(career: dict[str, CareerYears]):
    """
    Mutate the career dict passed, by removing entries which are only ever
    listed as a career_aliases entry in some page. Merge them to their primary name.
    """
    all_names = load_names_with_aliases()
    for main_name, aliases in all_names.items():
        for alias in aliases:
            if alias not in career: continue
            c = career.pop(alias)
            career[main_name] = merge_years(career.get(main_name, {}), c)

def main():
    years_active = {}
    career = {}
    cwd = Path.cwd()

    events_dir = cwd / "content/e"
    # Omit _index.md pages
    event_pages = events_dir.glob("**/????-??-??-*.md")

    for path in event_pages:
        page = Page(path)
        card = page.card
        if not card.matches:
            print("No card available, skipping")
            continue
        update_years_active(years_active, page)
        update_career(career, page)

    merge_aliases(career)

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
