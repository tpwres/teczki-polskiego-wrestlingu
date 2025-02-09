import json
import sqlite3
from pathlib import Path
from page import all_event_pages, EventPage
from card import Match, NamedParticipant, NamedTeam, AdHocTeam

def main():
    conn = sqlite3.connect('tpw.sqlite3', isolation_level=None)
    init_schema(conn)

    for page in all_event_pages():
        if not page.card:
            print(f"No card in {page.path}, skipping")

        print(page.title)

        event_id = upsert_event(conn, page)
        for bout in page.card.matches:
            upsert_match(conn, event_id, page.event_date, bout)

        # TODO: Insert crew
        # TODO: Read talent pages and name_to_country, update people with country codes

def init_schema(connection):
    schema = Path(__file__).parent / "schema.sql"

    curs = connection.cursor()
    with schema.open('r') as fp:
        commands = fp.read()
        for cmd in commands.split(';'):
            curs.execute(cmd)

    connection.commit()

def upsert_event(connection, event_page):
    cursor = connection.cursor()
    query = """
        INSERT OR IGNORE
        INTO events(title, path, date, city, venue, orgs)
        VALUES (?, ?, ?, ?, ?, ?)
        RETURNING id
    """
    match event_page:
        case EventPage(path=path, title=name, event_date=date, city=city, venue=venue, orgs=orgs):
            path = event_page.path.relative_to(Path.cwd()).as_posix()
            cursor.execute(query, (name, path, date, city, venue, json.dumps(orgs)))
            (event_id, ) = cursor.fetchone()
            return event_id


def upsert_match(connection, event_id, event_date, bout):
    cursor = connection.cursor()
    query = """
        INSERT OR IGNORE
        INTO matches(event_id, date, sequence_number, stip, championships, result_details, no_compete, segment, notes)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        RETURNING id
    """

    participant_ids = list(upsert_people(connection, bout))
    match_id = None
    match bout:
        case Match(index=index, opponents=opponents, options=options, date=date):
            nc = options.get('nc', None)
            segment = options.get('g', None)
            championships = options.get('c', None)
            stip = options.get('s', None)
            if segment and isinstance(segment, str):
                details = segment
                segment = True
            else:
                details = options.get('r')
            notes = options.get('n', None)
            cursor.execute(query, (
                event_id,
                date or event_date,
                index,
                stip,
                championships,
                details,
                nc,
                segment,
                json.dumps(notes) if notes else None
            ))
            (match_id,) = cursor.fetchone()

    # Insert participants
    query = """
        INSERT OR REPLACE INTO match_participants(match_id, participant_id, participant_type, winner)
        VALUES (?, ?, ?, ?)
    """
    _name, winner_id, winner_type = participant_ids.pop(0)
    cursor.execute(query, (match_id, winner_id, winner_type, True))

    cursor.executemany(query,
                       [(match_id, p_id, p_type, False) for p_name, p_id, p_type in participant_ids])


def upsert_people(connection, bout):
    # Walk through all the participants of the match, and upsert them in the database
    # Add teams if necessary
    # Return a list of (name, id, type) where type is either person or team
    cursor = connection.cursor()
    for side in bout.opponents:
        for person_or_team in side:
            match person_or_team:
                case NamedParticipant(name=name, link=link, annotation=annotation):
                    person_id = upsert_one_person(cursor, name, link)
                    yield (name, person_id, 'person')
                case NamedTeam(team_name=team_name, members=members):
                    member_ids = [upsert_one_person(cursor, p.name, p.link) for p in members]
                    team_id = upsert_team(cursor, team_name, member_ids)
                    yield (team_name, team_id, 'team')
                case AdHocTeam(members=members):
                    member_ids = [upsert_one_person(cursor, p.name, p.link) for p in members]
                    team_id = upsert_team(cursor, None, member_ids)
                    yield (None, team_id, 'team')
                case _:
                    print(person_or_team)
                    raise KeyError


def upsert_one_person(cursor, name, link):
    query = """
        INSERT INTO people(name, slug)
        VALUES (?, ?)
        ON CONFLICT (slug) DO UPDATE
          SET aliases = CASE
             WHEN json_array_length(aliases) == 0 THEN
               IF(excluded.name != name, json_array(excluded.name), '[]')
             WHEN EXISTS(SELECT 1 FROM json_each(aliases) WHERE value = excluded.name) THEN
               aliases
             ELSE
               IF(excluded.name != name, json_insert(aliases, '$[#]', excluded.name), aliases)
             END
        ON CONFLICT(name) DO UPDATE SET name = name
        RETURNING id
    """
    slug = link.replace('@/w/', '').replace('.md', '') if link else None
    cursor.execute(query, (name, slug))
    (person_id, ) = cursor.fetchone()
    return person_id

def upsert_team(cursor, name, member_ids):
    query = """
        INSERT INTO teams(name) VALUES (?)
        ON CONFLICT DO UPDATE SET name = excluded.name
        RETURNING id
    """
    cursor.execute(query, (name,))
    (team_id, ) = cursor.fetchone()

    query = """
      INSERT INTO team_members(team_id, person_id)
      VALUES (?, ?)
    """
    cursor.executemany(query, [(team_id, person_id) for person_id in member_ids])
    return team_id


if __name__ == "__main__":
    main()
