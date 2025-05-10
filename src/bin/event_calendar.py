#! /usr/bin/env python3

from argparse import ArgumentParser
from icalendar import vText, vCalAddress
from icalendar.cal import Event as vEvent, Calendar
import json
from pathlib import Path
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from page import EventPage, VenuePage, OrgPage
from textwrap import dedent
from typing import cast, Optional, Callable

@dataclass
class Event:
    day: date
    title: str
    page_path: str

@dataclass
class Org:
    url: str
    full_name: str

@dataclass
class Venue:
    url: str
    full_name: str
    city: Optional[str]

def setup_calendar(title: Optional[str]):
    calendar = Calendar()
    calendar['VERSION'] = '2.0'
    calendar['PRODID'] = 'tpwres.pl/1.0'
    calendar['CALSCALE'] = 'GREGORIAN'
    calendar['X-WR-CALNAME'] = title or 'Polish Wrestling Events'
    calendar['X-WR-TIMEZONE'] = 'Europe/Warsaw'
    return calendar

def build_description(url, page):
    return dedent(f'''
        <a href="{url}">{page.title}</a>
    ''').strip()

Predicate = Callable[[EventPage], bool]

def generate_calendar(events_dir: Path, accept_event: Predicate, title: Optional[str]):
    calendar = setup_calendar(title)
    event_files = events_dir.glob("**/????-??-??-*.md")
    created_at = datetime.now()

    for evf in event_files:
        page = EventPage(evf, verbose=False)
        if not accept_event(page):
            continue

        if page.card.matches:
            end_date = max(m.date or page.event_date for m in page.card.matches)
        else:
            end_date = page.event_date

        end_date += timedelta(days=1)
        dtstart = page.event_date.strftime("%Y%m%d")
        dtend = end_date.strftime("%Y%m%d")

        event_url = evf.relative_to("content/e").with_suffix("")
        event = vEvent(
            dtstamp=created_at.strftime('%Y%m%dT%H%M%S'),
            dtstart=dtstart,
            dtend=dtend,
            summary=vText(page.title),
            # tzid='Europe/Warsaw',
            uid=evf.stem,
            url=f'https://tpwres.pl/e/{event_url}')

        for org in page.orgs:
            org_page = lookup_org(org)
            attn = vCalAddress(org_page.url)
            attn.params['CN'] = vText(org_page.full_name)
            attn.params['CUTYPE'] = 'GROUP'
            attn.params['ROLE'] = 'CHAIR'
            event.add('organizer', attn)

        taxonomies = cast(dict[str, list[str]], page.front_matter.get('taxonomies', {}))
        extra = cast(dict, page.front_matter.get('extra', {}))
        venue_id = taxonomies.get('venue', [None])[0]
        if venue := lookup_venue(venue_id):
            if venue.city:
                location = f'{venue.full_name}, {venue.city}'
            else:
                location = venue.full_name
            event.add('location', vText(location))
        else:
            # No venue but may have city
            if city := extra.get('city'):
                event.add('location', vText(city))

        event.add('description', build_description(event_url, page))
        calendar.add_component(event)
        # TODO: Read card, add to details

    print(calendar.to_ical().decode('utf-8'))


def lookup_org(code):
    path = Path('content/o') / f'{code}.md'
    page = OrgPage(path, verbose=False)
    return Org(
        url=f'https://tpwres.pl/o/{code}',
        full_name=cast(str, page.front_matter['title'])
    )

def lookup_venue(code):
    if not code: return None
    path = Path('content/v') / f'{code}.md'
    if not path.exists(): return None

    page = VenuePage(path, verbose=False)
    front_matter = page.front_matter
    extra = cast(dict[str, str], front_matter.get('extra', {}))
    return Venue(
        url=f'https://tpwres.pl/v/{code}',
        full_name=cast(str, front_matter['title']),
        city=extra.get('city', None)
    )


def main():
    parser = ArgumentParser(
        prog='build_calendar.py',
        description='Build iCal files out of event directories'
    )
    parser.add_argument(
        'events_dir',
        nargs='?',
        help='Directory name to parse event files from. If omitted, loads all event files available from under content/e'
    )
    parser.add_argument(
        '-V', '--venue',
        action='store',
        metavar='VENUE',
        help='Only add event if its frontmatter specifies a venue and it matches the provided value. '
        'Rejects events with no venue.'
    )
    parser.add_argument(
        '-C', '--city',
        action='store',
        metavar='CITY',
        help='Only add event if its frontmatter specifies city and it matches the provided value'
    )
    parser.add_argument(
        '-t', '--title',
        action='store',
        metavar='TITLE',
        help='Set title for the calendar'
    )
    opts = parser.parse_args()

    def event_filter(page: EventPage) -> bool:
        front_matter = cast(dict, page.front_matter)
        extra = cast(dict, front_matter.get('extra', {}))
        fm_city = extra.get('city', None)
        if opts.city and fm_city and opts.city != fm_city:
            return False

        taxonomies = cast(dict, front_matter.get('taxonomies', {}))
        fm_venue = taxonomies.get('venue', [None])[0]
        # If opts.venue is specified, but the event has no venue info, reject it
        if fm_venue is None and opts.venue:
            return False
        # Otherwise, compare the two
        if opts.venue and fm_venue and opts.venue != fm_venue:
            return False

        return True

    generate_calendar(Path(opts.events_dir or 'content/e'), event_filter, opts.title)

if __name__ == "__main__":
    main()
