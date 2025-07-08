from card import Match, Name, Fighter, Manager, AdHocTeam, NamedTeam, MatchParseError, Team
from datetime import date
from typing import Iterable
import pytest

def test_match_init_basic():
    # Simple match with two opponents
    match = Match(["El Dragón", "Rey Misterioso"], 0, None)
    assert len(match.opponents) == 2
    assert match.index == 0
    assert match.date is None
    assert match.options == {}

def test_match_init_with_options():
    # Match with options dictionary
    match = Match(["El Rudo", "Místico", {"s": "Lucha Extrema"}], 1, date(2023, 1, 1))
    assert len(match.opponents) == 2
    assert match.date == date(2023, 1, 1)
    assert match.options == {"s": "Lucha Extrema"}

def test_match_init_only_options():
    # Match with only options dictionary
    match = Match({"d": "Main Event"}, 2, None)
    assert len(match.opponents) == 0
    assert match.options == {"d": "Main Event"}

def test_parse_opponents():
    match = Match([], 0, None)
    opponents = list(match.parse_opponents(["El Capitán", "Águila Dorada"]))
    assert len(opponents) == 2, "parse_opponents should return two opponent sides"
    assert all(isinstance(o, Iterable) for o in opponents), "Each opponent should be an iterable"

def test_parse_opponents_with_teams():
    match = Match([], 0, None)
    opponents = list(match.parse_opponents(["Los Guerreros: El Capitán, Águila Dorada + Máscara Roja", "Máximo, Diamante"]))
    assert len(opponents) == 2, "parse_opponents should return two opponent sides"
    assert all(isinstance(o, Iterable) for o in opponents), "Each opponent should be an iterable"
    assert len(opponents[0]) == 2, "First opponent side should have 2 participants"
    assert isinstance(opponents[0][0], NamedTeam), "First participant should be a team"
    assert isinstance(opponents[0][1], Fighter), "Second participant should be a fighter"
    assert len(opponents[0][0].members) == 2, "Team in first opponent should have 2 participants"
    assert isinstance(opponents[1][0], AdHocTeam), "Second opponent side should be an AdHocTeam"
    assert len(opponents[1][0].members) == 2, "Second opponent side should have 2 participants"

def test_parse_opponents_empty_side():
    match = Match([], 0, None)
    with pytest.raises(MatchParseError, match="at least one side.*empty"):
        list(match.parse_opponents(["Máscara Roja", None]))

def test_parse_opponents_invalid_type():
    match = Match([], 0, None)
    with pytest.raises(MatchParseError, match="Unexpected match participant"):
        list(match.parse_opponents(["El Guerrero", 123]))

def test_parse_partners():
    match = Match([], 0, None)
    partners = ["El Tigre", "Tornado Negro"]
    result = list(match.parse_partners(partners))
    assert len(result) == 2, "parse_partners should return one participant per name"
    assert all(isinstance(p, Fighter) for p in result), "All participants should be Fighter instances"

def test_parse_maybe_team_single_wrestler():
    match = Match([], 0, None)
    result = match.parse_maybe_team("El Relámpago")
    assert isinstance(result, Fighter), "Single wrestler should be parsed as a Fighter"
    assert result.name == "El Relámpago", "Fighter name should be preserved"

def test_parse_maybe_team_adhoc_team():
    match = Match([], 0, None)
    result = match.parse_maybe_team("El Rayo, Volcán Azul")
    assert isinstance(result, AdHocTeam), "Multiple wrestlers should be parsed as an AdHocTeam"
    assert len(result.members) == 2, "AdHocTeam should contain all wrestlers"

def test_parse_maybe_team_named_team():
    match = Match([], 0, None)
    result = match.parse_maybe_team("Los Conquistadores: El Diablo, Serpiente Verde")
    assert isinstance(result, NamedTeam), "Team with a name should be parsed as a NamedTeam"
    assert result.team_name == "Los Conquistadores", "Team name should be preserved"
    assert len(result.members) == 2, "NamedTeam should contain all wrestlers"

def test_parse_maybe_team_named_team_with_link():
    match = Match([], 0, None)
    result = match.parse_maybe_team("[Los Destructores](team-link): El Jaguar, Cometa Rojo")
    assert isinstance(result, NamedTeam), "Team with a name and link should be parsed as a NamedTeam"
    assert result.team_name == "Los Destructores", "Team name should be preserved"
    assert result.link == "team-link", "Team link should be preserved"
    assert len(result.members) == 2, "NamedTeam should contain all wrestlers"

def test_all_names():
    match = Match(["El Mago", "La Furia"], 0, None)
    names = list(match.all_names())
    assert len(names) == 2, "all_names should return all wrestlers' names"
    assert all(isinstance(n, Name) for n in names), "Each name should be a Name instance"

def test_all_names_indexed():
    match = Match(["Rey Dragón", "El Fantasma"], 0, None)
    names_indexed = list(match.all_names_indexed())
    assert len(names_indexed) == 2, "all_names_indexed should return all wrestlers' names with indices"
    assert all(isinstance(n[0], int) and isinstance(n[1], Name) for n in names_indexed), "Each entry should be a tuple of (index, Name)"

def test_all_teams_indexed():
    match = Match(["Los Hermanos: El Fuego, El Hielo", "El Lobo Solitario"], 0, None)
    teams_indexed = list(match.all_teams_indexed())
    assert len(teams_indexed) == 1, "all_teams_indexed should return only team entries"
    assert teams_indexed[0][0] == 0, "Team index should match its position in the match"
    assert isinstance(teams_indexed[0][1], Team), "Second element should be a Team instance"

def test_winner():
    match = Match(["Winner(c)", "Loser", {"c": "[Campeonato Mundial Peso Completo](@/titles/championship.md)"}], 0, None)
    winner = list(match.winner())
    assert len(winner) == 1, "winner should return the first side of the match"
    assert isinstance(winner[0], Fighter), "Winner should be a Fighter instance"
    assert winner[0].name == "Winner", "Winner name should be preserved"

def test_tag_team_match():
    match = Match(["Los Invencibles(c): El Halcón, El Trueno", "Los Diablos: El Demonio, Fuego Salvaje", {"c": "[Campeonato de Parejas LMX](@/titles/tag-team.md)"}], 0, None)
    assert len(match.opponents) == 2

    # Each opponent is an iterable containing teams/participants
    team_alpha = list(match.opponents[0])[0]
    team_beta = list(match.opponents[1])[0]

    assert isinstance(team_alpha, NamedTeam)
    assert isinstance(team_beta, NamedTeam)
    assert team_alpha.team_name == "Los Invencibles"
    assert team_beta.team_name == "Los Diablos"
    assert len(team_alpha.members) == 2
    assert len(team_beta.members) == 2

def test_match_with_managers():
    match = Match(["El Conquistador w/ Don Ricardo", "Huracán Negro w/ Señor Martínez"], 0, None)
    assert len(match.opponents) == 2

    fighter_a_group = list(match.opponents[0])
    fighter_b_group = list(match.opponents[1])

    # Each side has one AdHocTeam containing both Fighter and Manager
    assert len(fighter_a_group) == 1
    assert len(fighter_b_group) == 1

    # Check that the AdHocTeam contains the expected members
    assert isinstance(fighter_a_group[0], AdHocTeam)
    assert isinstance(fighter_b_group[0], AdHocTeam)

    # Check team members
    assert len(fighter_a_group[0].members) == 2
    assert len(fighter_b_group[0].members) == 2
    assert isinstance(fighter_a_group[0].members[0], Fighter)
    assert isinstance(fighter_a_group[0].members[1], Manager)
    assert isinstance(fighter_b_group[0].members[0], Fighter)
    assert isinstance(fighter_b_group[0].members[1], Manager)

def test_invalid_match_format():
    with pytest.raises(MatchParseError, match="Malformed participant name"):
        Match(["[Malformed Link(fighter)", "El Puma"], 0, None)

def test_complex_tag_team_match():
    match = Match([
        "Los Reyes: [El Rey](@/w/el-rey.md), [El Príncipe](@/w/el-principe.md) w/ [Don Eduardo](@/w/don-eduardo.md)",
        "Los Técnicos: [Máscara Azul](@/w/mascara-azul.md) & [Rayo Veloz](@/w/rayo-veloz.md)",
        {"s": "Tornado Tag Match", "r": "DQ"}
    ], 0, None)

    team_alpha = list(match.opponents[0])[0]
    team_beta = list(match.opponents[1])[0]

    # Check team names
    assert team_alpha.team_name == "Los Reyes"
    assert team_beta.team_name == "Los Técnicos"

    # Check team members
    assert len(team_alpha.members) == 3  # 2 fighters + 1 manager
    assert team_alpha.members[0].name == "El Rey"
    assert team_alpha.members[1].name == "El Príncipe"
    assert team_alpha.members[2].name == "Don Eduardo"

    assert len(team_beta.members) == 2  # 2 fighters
    assert team_beta.members[0].name == "Máscara Azul"
    assert team_beta.members[1].name == "Rayo Veloz"

def test_all_teams_indexed_empty():
    match = Match(["Último Guerrero", "Atlantis"], 0, None)
    teams_indexed = list(match.all_teams_indexed())
    assert len(teams_indexed) == 0  # No teams, only individual fighters

def test_canonicalize_name():
    match = Match(["[Fancy-Name O'Wrestler](@/w/fancy-name-o-wrestler.md)", "Simple Name"], 0, None)

    fancy = list(match.opponents[0])[0]
    simple = list(match.opponents[1])[0]

    # Test canonicalization of names with and without links
    assert fancy.canonicalize() == "fancy-name-o-wrestler"
    assert simple.canonicalize() == "simple-name"

def test_match_with_linked_names():
    match = Match(["[Fighter A](@/w/fighter-a.md)", "[Fighter B](@/w/fighter-b.md)", {"g": "Segment Title"}], 0, None)

    fighter_a = list(match.opponents[0])[0]
    fighter_b = list(match.opponents[1])[0]

    assert fighter_a.name == "Fighter A", "Fighter name should be extracted from markdown link"
    assert fighter_a.link == "@/w/fighter-a.md", "Fighter link should be preserved from markdown link"
    assert fighter_b.name == "Fighter B", "Fighter name should be extracted from markdown link"
    assert fighter_b.link == "@/w/fighter-b.md", "Fighter link should be preserved from markdown link"

def test_match_with_empty_opponents():
    match = Match({"date": "2023-05-15"}, 0, None)
    assert len(match.opponents) == 0, "Special rows should have no opponents"
    assert match.options == {"date": "2023-05-15"}, "Options should be preserved"

def test_match_with_date():
    test_date = date(2023, 5, 15)
    match = Match(["Fighter A", "Fighter B", {"nc": "upcoming"}], 1, test_date)
    assert match.date == test_date
    assert match.options == {"nc": "upcoming"}

def test_match_with_multiple_options():
    match = Match(["Fighter A", "Fighter B", {
        "s": "No DQ",
        "c": "[Campeonato Nacional Mexicano](@/titles/championship.md)",
        "n": ["Note 1", "Note 2"]
    }], 0, None)
    assert match.options == {
        "s": "No DQ",
        "c": "[Campeonato Nacional Mexicano](@/titles/championship.md)",
        "n": ["Note 1", "Note 2"]
    }

def test_match_with_result_option():
    match = Match(["Winner", "Loser", {"r": "DQ"}], 0, None)
    assert match.options == {"r": "DQ"}

def test_match_with_no_contest_option():
    match = Match(["Fighter A", "Fighter B", {"nc": "Time-limit Draw"}], 0, None)
    assert match.options == {"nc": "Time-limit Draw"}

def test_match_with_nc_r_exclusivity():
    # Test that nc and r options cannot be used together
    with pytest.raises(MatchParseError, match="Match.*cannot use both 'nc' and 'r' options together"):
        Match(["El Campeón", "El Retador", {"nc": "Time-limit Draw", "r": "DQ"}], 0, None)

    # Test that nc and r options cannot be used together in a segment
    with pytest.raises(MatchParseError, match="Segment.*cannot use both 'nc' and 'r' options together"):
        Match(["El Campeón", "El Retador", {"g": "Promo Segment", "nc": "Time-limit Draw", "r": "DQ"}], 0, None)

def test_match_with_unknown_result():
    match = Match(["Fighter A", "Fighter B", {"nc": "?"}], 0, None)
    assert match.options == {"nc": "?"}

def test_match_as_segment():
    # g=True with s as a non-empty string is valid
    match = Match(["Superstar A", "Superstar B", {"g": True, "s": "Contract Signing"}], 0, None)
    assert match.options == {"g": True, "s": "Contract Signing"}

    # g=True without s should raise an error
    with pytest.raises(MatchParseError, match="Segment.*must have a non-empty stipulation"):
        Match(["Superstar A", "Superstar B", {"g": True}], 0, None)

    # g=True with empty s should raise an error
    with pytest.raises(MatchParseError, match="Segment.*must have a non-empty stipulation"):
        Match(["Superstar A", "Superstar B", {"g": True, "s": ""}], 0, None)

def test_match_as_segment_with_description():
    # g as a string is valid
    match = Match(["Superstar A", "Superstar B", {"g": "Contract Signing"}], 0, None)
    assert match.options == {"g": "Contract Signing"}

    # g as a non-boolean, non-string value should raise an error
    with pytest.raises(MatchParseError, match="Segment.*description must be a non-empty string"):
        Match(["Superstar A", "Superstar B", {"g": 123}], 0, None)

    # g as an empty string should also be rejected
    with pytest.raises(MatchParseError, match="Segment.*description must be a non-empty string"):
        Match(["Superstar A", "Superstar B", {"g": ""}], 0, None)

def test_match_with_single_note():
    match = Match(["Fighter A", "Fighter B", {"n": "Special Guest Referee: Superstar C"}], 0, None)
    assert match.options == {"n": "Special Guest Referee: Superstar C"}

def test_special_row_with_delimiter():
    match = Match({"d": "Day 2"}, 0, None)
    assert len(match.opponents) == 0
    assert match.options == {"d": "Day 2"}

def test_special_row_with_date():
    match = Match({"date": "2023-11-19"}, 0, None)
    assert len(match.opponents) == 0
    assert match.options == {"date": "2023-11-19"}

def test_special_row_with_combined_options():
    match = Match({"d": "Day 2", "date": "2023-11-19"}, 0, None)
    assert len(match.opponents) == 0
    assert match.options == {"d": "Day 2", "date": "2023-11-19"}

def test_special_row_with_credits():
    match = Match({"credits": {"Referees": "John Smith", "Ring announcer": "Jane Doe"}}, 0, None)
    assert len(match.opponents) == 0
    assert match.options == {"credits": {"Referees": "John Smith", "Ring announcer": "Jane Doe"}}

def test_special_row_rejects_invalid_options():
    # Test that only allowed special row options are accepted as standalone options

    # Test invalid options (not in SPECIAL_ROW_ALLOWED_OPTIONS)
    invalid_options = ["s", "r", "nc", "g", "n"]
    for invalid_option in invalid_options:
        with pytest.raises(MatchParseError, match="Special row.*invalid options"):
            Match({invalid_option: "Test Value"}, 0, None)

    # Test all valid options individually
    for valid_option in Match.SPECIAL_ROW_ALLOWED_OPTIONS:
        if valid_option == "credits":
            # Credits option requires a dict value
            Match({valid_option: {"Referees": "John Smith"}}, 0, None)
        else:
            # Other options can take a string value
            Match({valid_option: "Test Value"}, 0, None)

    # Test combinations of valid options
    Match({"d": "Day 2", "date": "2023-11-19"}, 0, None)
    Match({"d": "Day 2", "credits": {"Referees": "John Smith"}}, 0, None)
    Match({"date": "2023-11-19", "credits": {"Referees": "John Smith"}}, 0, None)
    Match({"d": "Day 2", "date": "2023-11-19", "credits": {"Referees": "John Smith"}}, 0, None)

def test_regular_match_rejects_special_row_options():
    # Test that special row options are not allowed in regular match rows
    for special_option in Match.SPECIAL_ROW_ALLOWED_OPTIONS:
        with pytest.raises(MatchParseError, match="special row options not allowed in regular match"):
            if special_option == "credits":
                # Credits option requires a dict value
                Match(["Fighter A", "Fighter B", {special_option: {"Referees": "John Smith"}}], 0, None)
            else:
                Match(["Fighter A", "Fighter B", {special_option: "Test Value"}], 0, None)

    # Regular match options should work fine
    Match(["Fighter A", "Fighter B", {"s": "No DQ"}], 0, None)
    Match(["Fighter A", "Fighter B", {"r": "DQ"}], 0, None)
    Match(["Fighter A", "Fighter B", {"nc": "Time-limit Draw"}], 0, None)
    Match(["Fighter A", "Fighter B", {"g": True, "s": "Segment"}], 0, None)
    Match(["Fighter A", "Fighter B", {"g": "Promo Segment"}], 0, None)
    Match(["Fighter A", "Fighter B", {"n": "Special Note"}], 0, None)

def test_match_opponent_count():
    # Test with more than two opponents
    match = Match(["Fighter A", "Fighter B", "Fighter C", {"nc": "Triple Threat"}], 0, None)
    assert len(match.opponents) == 3

    # Each opponent should be an iterable with a Fighter
    assert isinstance(list(match.opponents[0])[0], Fighter)
    assert isinstance(list(match.opponents[1])[0], Fighter)
    assert isinstance(list(match.opponents[2])[0], Fighter)
