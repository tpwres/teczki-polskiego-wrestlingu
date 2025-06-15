#! /usr/bin/env python3

import re
from utils import accepted_name
from card import Match, CardParseError, teams_in_match
from page import EventPage
from pathlib import Path
from datetime import date
import json
from sys import stderr, exit

class MatchEncoder(json.JSONEncoder):
    def default(self, obj):
        match obj:
            case Match():
                return obj.line
            case date():
                return obj.strftime("%Y-%m-%d")
            case _:
                return super().default(obj)

def main():
    num_errors = 0
    appearances = {}
    crew_appearances = {}
    all_bouts = []
    cwd = Path.cwd()
    # 1. List all event pages
    content_dir = cwd / 'content'
    events_dir = content_dir / "e"
    event_pages = events_dir.glob("**/????-??-??-*.md")
    # 2. For each event page, determine it's organization (can be more than one) from page name or frontmatter
    global_match_num = 0

    for path in event_pages:
        relative_path = path.relative_to(content_dir).as_posix()
        try:
            page = EventPage(path, verbose=False)
            card = page.card
            if not card.matches:
                all_bouts.append(placeholder_entry(page, relative_path, global_match_num))
                global_match_num += 1
                continue
        except CardParseError:
            num_errors += 1
            continue

        for bout in card.matches:
            info = match_entry(page, bout, relative_path, global_match_num, params=card.params)

            all_bouts.append(info)

            for index, person in bout.all_names_indexed():
                if not accepted_name(person.name): continue
                bouts = appearances.setdefault(person.name, [])
                bouts.append((global_match_num, index))

            for index, team in bout.all_teams_indexed():
                for key in team.build_keys():
                    bouts = appearances.setdefault(key, [])
                    bouts.append((global_match_num, index))

            global_match_num += 1

        if not card.crew: continue

        for person in card.crew.members:
            if not accepted_name(person.name): continue
            events = crew_appearances.setdefault(person.name, [])
            events.append(
                dict(
                    d=page.event_date,
                    o=page.orgs,
                    n=page.title,
                    p=relative_path,
                    r=person.role
                )
            )

    if num_errors > 0:
        stderr.write("Errors found, aborting\n")
        exit(1)

    app_simple = {name: [apr[0] for apr in bouts] for name, bouts in appearances.items()}
    save_json('appearances.json', app_simple)
    save_json('appearances_v2.json', appearances)
    save_json('crew_appearances.json', crew_appearances)
    save_json('all_matches.json', all_bouts)

def save_json(filename, obj, message=None):
    data_dir = Path.cwd() / 'data'
    data_dir.mkdir(exist_ok=True)

    with (data_dir / filename).open('w') as f:
        if message:
            print(message)
        json.dump(obj, f, cls=MatchEncoder)

def match_entry(page, bout, rel_path, num, params):
    predicted = params.get('predicted', False)
    incomplete = params.get('incomplete', False)
    unofficial = params.get('unofficial', False)
    info = dict(
        d=bout.date or page.event_date,
        o=page.orgs,
        n=page.title,
        m=bout,
        p=rel_path,
        i=num
    )
    if predicted:
        info['tt'] = 'predicted'
    elif incomplete:
        info['tt'] = 'incomplete'
    elif unofficial:
        info['tt'] = 'unofficial'

    return info


def placeholder_entry(page: EventPage, rel_path, num) -> dict:
    return dict(
        d=page.event_date,
        o=page.orgs,
        n=page.title,
        m=None,
        p=rel_path,
        i=num
    )

if __name__ == "__main__":
    main()
