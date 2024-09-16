import json
import sqlite3

def main():
    conn = sqlite3.connect('tpw.sqlite3', autocommit=True)
    curs = conn.cursor()
    # Load schema
    with open('schema.sql', 'r') as fp:
        commands = fp.read()
        for cmd in commands.split(';'):
            curs.execute(cmd)

    # Load all_matches
    with open('data/all_matches.json') as fp:
        all_matches = json.load(fp)
        for mm in all_matches:
            match mm:
                case {'d': date, 'o': orgs, 'n': name, 'm': participants_options, 'p': path}:
                    event_id = upsert_event(curs, name, path, date, orgs)
                    print(event_id)
                    insert_matches(curs, event_id, participants_options)
                    break

def upsert_event(cursor, name, path, date, orgs):
    res = cursor.execute("""
        INSERT OR IGNORE
        INTO events(title, path, date, orgs)
        VALUES (?, ?, ?, ?)
        RETURNING id
    """, (name, path, date, json.dumps(orgs)))
    res = cursor.execute("SELECT id FROM events where path = ?", (path,))
    (event_id, ) = res.fetchone()
    return event_id


def insert_matches(cursor, event_id, participants_options):
    match participants_options:
        case [*p, dict(o)]:
            participants = p
            options = o
        case [*p]:
            participants = p
            options = {}
    print(participants)
    print(options)


if __name__ == "__main__":
    main()
