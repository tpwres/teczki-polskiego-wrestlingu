#! /usr/bin/env python3

import argparse
from pathlib import Path
from collections import Counter
import json
from typing import cast
from utils import RichEncoder, accepted_name
from card import CardParseError, names_in_match, teams_in_match
from page import EventPage
from sys import stderr, exit
from content import FilesystemTree, ZipContentTree

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

def load_names_with_aliases(content) -> dict[str, set[str]]:
    name_files = content.glob('content/w/*.md')
    names = {}
    for stream in name_files:
        path = Path(stream.name)
        if path.name == '_index.md': continue
        if path.name.startswith('.'): continue

        talent = content.page(stream)
        match talent.front_matter:
            case {"extra": dict(extra), "title": str(title)}:
                preferred_name = extra.get('career_name', title)
                names[preferred_name] = set([])
                aliases = extra.get('career_aliases', [])
                names[preferred_name] |= set(cast(list[str], aliases))

    return names

def merge_aliases(content, career: dict[str, CareerYears]):
    """
    Mutate the career dict passed, by removing entries which are only ever
    listed as a career_aliases entry in some page. Merge them to their primary name.
    """
    all_names = load_names_with_aliases(content)
    for main_name, aliases in all_names.items():
        for alias in aliases:
            if alias not in career: continue
            c = career.pop(alias)
            career[main_name] = merge_years(career.get(main_name, {}), c)

def process(content, output_path):
    careers = {}
    careers_by_file = {}
    team_careers = {}
    team_cbf = {}
    num_errors = 0

    # Omit _index.md pages
    event_pages = content.glob("content/e/**/????-??-??-*.md")

    for event_file in event_pages:
        try:
            page = EventPage(event_file, verbose=False)
            card = page.card
            if not card.matches:
                stderr.write(f"{page.path}: Warning: no card available, skipping\n")
                continue
            update_career(careers, team_careers, page)
            update_cbf(careers_by_file, team_cbf, page)
        except CardParseError:
            num_errors += 1

    if num_errors > 0:
        stderr.write("Errors found, aborting\n")
        exit(1)

    merge_aliases(content, careers)

    data_dir = output_path
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
    cwd = Path.cwd()
    parser = argparse.ArgumentParser(prog='build-metadata')
    parser.add_argument('-z', '--zipfile')
    args = parser.parse_args()
    if args.zipfile:
        content = ZipContentTree(Path(args.zipfile.strip()))
    else:
        content = FilesystemTree(cwd)

    output_dir = cwd / 'data'
    process(content, output_dir)
