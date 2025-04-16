#! /usr/bin/env python3

from pathlib import Path
from collections import Counter
from articles import load_names_with_aliases
import json
from typing import cast
from utils import RichEncoder, accepted_name
from card import CardParseError, names_in_match, teams_in_match
from page import EventPage
from sys import stderr, exit

OrgYears = dict[str, int]
CareerYears = dict[int, OrgYears]

def update_cbf(careers, team_careers, page: EventPage):
    event_date = page.event_date
    orgs = page.orgs
    card = page.card

    if not card.matches:
        return

    if not event_date:
        return

    for mm in card.matches:
        names = names_in_match(mm)

        for person in names:
            if not accepted_name(person.name): continue
            key = person.link or person.name

            entry = careers.setdefault(key, {})
            year = cast(Counter, entry.setdefault(event_date.year, Counter()))
            year.update(orgs)

        teams = teams_in_match(mm)
        for team in teams:
            for key in team.build_keys():
                entry = team_careers.setdefault(key, {})
                year = cast(Counter, entry.setdefault(event_date.year, Counter()))
                year.update(orgs)

    if not card.crew:
        return

    for person in card.crew.members:
        if not accepted_name(person.name):
            continue
        key = person.link or person.name

        entry = careers.setdefault(key, {})
        year = cast(Counter, entry.setdefault(event_date.year, Counter()))
        year.update(orgs)



def update_career(career: dict[str, CareerYears], team_careers: dict[str, CareerYears], page: EventPage):
    event_date = page.event_date
    orgs = page.orgs
    card = page.card

    if not card.matches:
        return

    if not event_date:
        return

    for mm in card.matches:
        names = names_in_match(mm)

        # If a person appeared in more than one match on the card, count it appropriately
        for person in names:
            plain = person.name
            if not accepted_name(plain): continue

            entry = career.setdefault(plain, {})
            year = cast(Counter, entry.setdefault(event_date.year, Counter()))
            year.update(orgs)

        teams = teams_in_match(mm)
        for team in teams:
            for key in team.build_keys():
                entry = team_careers.setdefault(key, {})
                year = cast(Counter, entry.setdefault(event_date.year, Counter()))
                year.update(orgs)

    if not card.crew:
        return

    for person in card.crew.members:
        if not accepted_name(person.name):
            continue
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
    careers = {}
    careers_by_file = {}
    team_careers = {}
    team_cbf = {}
    cwd = Path.cwd()
    num_errors = 0

    events_dir = cwd / "content/e"
    # Omit _index.md pages
    event_pages = events_dir.glob("**/????-??-??-*.md")

    for path in event_pages:
        try:
            page = EventPage(path, verbose=False)
            card = page.card
            if not card.matches:
                stderr.write(f"{path}: Warning: no card available, skipping\n")
                continue
            update_career(careers, team_careers, page)
            update_cbf(careers_by_file, team_cbf, page)
        except CardParseError:
            num_errors += 1

    if num_errors > 0:
        stderr.write("Errors found, aborting\n")
        exit(1)

    merge_aliases(careers)

    data_dir = cwd / 'data'
    data_dir.mkdir(exist_ok=True)

    with (data_dir / 'career.json').open('w') as f:
        print("Saving career to %s" % f.name)
        json.dump(careers, f, cls=RichEncoder)

    with (data_dir / 'career_v2.json').open('w') as f:
        print("Saving career v2 to %s" % f.name)
        json.dump(careers_by_file, f, cls=RichEncoder)

    with (data_dir / 'team_careers.json').open('w') as f:
        print("Saving team career v2 to %s" % f.name)
        json.dump(team_cbf, f, cls=RichEncoder)


if __name__ == "__main__":
    main()
