#! /usr/bin/env python3

from utils import accepted_name
from card import Card, Match, CardParseError
from rich_doc import RichDoc
from sink import ExplosiveSink, ConsoleSink
from page import EventPage
from pathlib import Path
from datetime import date
import json
from sys import stderr, exit

class MatchEncoder(json.JSONEncoder):
    def default(self, o):
        match o:
            case Match():
                return o.line
            case date():
                return o.strftime("%Y-%m-%d")
            case _:
                return super().default(o)

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
    sink = ConsoleSink()
    for path in event_pages:
        print(path)
        try:
            doc = RichDoc.from_file(path, sink)
            card_section = doc.card_section
            if not card_section:
                continue
            card = Card(card_section, doc, sink)
            if not card.matches:
                continue
        except CardParseError:
            num_errors += 1
            continue

        page = EventPage(doc)
        relative_path = path.relative_to(content_dir).as_posix()
        predicted = card.params.get('predicted', False)
        incomplete = card.params.get('incomplete', False)
        unofficial = card.params.get('unofficial', False)

        for bout in card.matches:
            info = dict(
                d=bout.date or page.event_date,
                o=page.orgs,
                n=page.title,
                m=bout,
                p=relative_path,
                i=global_match_num
            )
            if predicted:
                info['tt'] = 'predicted'
            elif incomplete:
                info['tt'] = 'incomplete'
            elif unofficial:
                info['tt'] = 'unofficial'

            all_bouts.append(info)

            for index, person in bout.all_names_indexed():
                if not accepted_name(person.name): continue
                bouts = appearances.setdefault(person.name, [])
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

    data_dir = cwd / 'data'
    data_dir.mkdir(exist_ok=True)

    with (data_dir / 'appearances.json').open('w') as f:
        print("Saving appearance map to %s" % f.name)
        app_simple = {name: [apr[0] for apr in bouts] for name, bouts in appearances.items()}
        json.dump(app_simple, f)

    with (data_dir / 'appearances_v2.json').open('w') as f:
        print("Saving appearance map v2 to %s" % f.name)
        json.dump(appearances, f)

    with (data_dir / 'crew_appearances.json').open('w') as f:
        print("Saving crew appearance map to %s" % f.name)
        json.dump(crew_appearances, f, cls=MatchEncoder)

    with (data_dir / 'all_matches.json').open('w') as f:
        print("Saving all matches to %s" % f.name)
        json.dump(all_bouts, f, cls=MatchEncoder)

if __name__ == "__main__":
    main()
