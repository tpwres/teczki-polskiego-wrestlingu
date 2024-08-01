#! /usr/bin/env python3

from icalendar import vText, vCalAddress
from icalendar.cal import Event, Calendar
import json
from pathlib import Path
from dataclasses import dataclass
from datetime import date
from page import Page

@dataclass
class EventPage:
    day: date
    title: str
    page_path: str

@dataclass
class OrgPage:
    url: str
    full_name: str

@dataclass
class VenuePage:
    url: str
    full_name: str
    city: str

def main():
    calendar = Calendar()
    calendar['VERSION'] = '2.0'
    calendar['CALSCALE'] = 'GREGORIAN'
    calendar['METHOD'] = 'PUBLISH'
    calendar['X-WR-CALNAME'] = 'Polish Wrestling Events'
    calendar['X-WR-TIMEZONE'] = 'Europe/Warsaw'
    # Not from all-matches, it doesn't have future events
    all_matches = json.load(Path("data/all_matches.json").open('rb'))
    event_files = Path("content/e").glob("**/????-??-??-*.md")

    for evf in event_files:
        page = Page(evf, verbose=False)
        event = Event()
        event.add('dtstart', page.event_date)
        event.add('summary', vText(page.event_name))
        event.add('tzid', 'Europe/Warsaw')
        event.add('url', f'https://tpwres.pl/e/{evf.relative_to("content/e").with_suffix("")}')
        for org in page.orgs:
            org_page = lookup_org(org)
            attn = vCalAddress(org_page.url)
            attn.params['cn'] = vText(org_page.full_name)
            attn.params['CUTYPE'] = 'GROUP'
            # attn.params['ROLE'] = 'CHAIR'
            event.add('organizer', attn)
        venue_id = page.front_matter.get('taxonomies', {}).get('venue', [None])[0]
        if venue := lookup_venue(venue_id):
            if venue.city:
                location = f'{venue.full_name}, {venue.city}'
            else:
                location = venue.full_name
            event.add('location', vText(location))

        calendar.add_component(event)
        # TODO: Find venue page, add info
        # TODO: Read card, add to details

    print(calendar.to_ical().decode('utf-8'))


def lookup_org(code):
    path = Path('content/o') / f'{code}.md'
    page = Page(path, verbose=False)
    return OrgPage(
        url=f'https://tpwres.pl/o/{code}',
        full_name=page.front_matter['title']
    )

def lookup_venue(code):
    if not code: return None
    path = Path('content/v') / f'{code}.md'
    if not path.exists(): return None

    page = Page(path, verbose=False)
    return VenuePage(
        url=f'https://tpwres.pl/v/{code}',
        full_name=page.front_matter['title'],
        city=page.front_matter.get('extra', {}).get('city', None)
    )



if __name__ == "__main__":
    main()
