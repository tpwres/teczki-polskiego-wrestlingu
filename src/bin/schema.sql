DROP TABLE IF EXISTS events;
CREATE TABLE events(
  id integer primary key,
  title text not null,
  path text not null,
  date date not null,
  city text,
  -- Switch to foreign key to events table
  venue text,
  -- Normalization: should be a m2m table orgs_events instead
  orgs blob
);
CREATE UNIQUE INDEX IF NOT EXISTS events_path_unique ON events(path);

DROP TABLE IF EXISTS matches;
CREATE TABLE matches(
  id integer primary key,
  event_id integer not null,
  date date not null, -- Event date, or exact date for multi-day
  sequence_number integer, -- Number in card
  stip text,
  championships text,
  result_details text,
  no_compete text,
  segment bool,
  notes blob
);

DROP TABLE IF EXISTS match_participants;
CREATE TABLE match_participants(
  match_id integer not null,
  -- foreign key to people or teams
  participant_id integer not null,
  -- indicates participant flavor: 'person' or 'team'
  participant_type text,
  winner bool
);

DROP TABLE IF EXISTS teams;
CREATE TABLE teams(
  id integer primary key,
  -- null if adhoc team
  name text
);
CREATE UNIQUE INDEX IF NOT EXISTS teams_unique ON teams(name);

DROP TABLE IF EXISTS people;
CREATE TABLE people(
  id integer primary key,
  name text,
  aliases blob default '[]',
  slug text
);
CREATE UNIQUE INDEX IF NOT EXISTS people_unique_slug ON people(slug);
CREATE UNIQUE INDEX IF NOT EXISTS people_unique_names ON people(name);

DROP TABLE IF EXISTS team_members;
CREATE TABLE team_members(
  team_id integer, -- references teams
  person_id integer
);
