import pytest

from card import Card, Match
from card import Fighter as F, Manager as M
import metadata
import yaml

def parse_match(text):
    matchrow = yaml.safe_load(text)
    return Match(matchrow, 0, None)

def test_basic_names():
    m = parse_match("[Tadeusz Kościuszko, George Washington]")
    names = metadata.names_in_match(m)
    assert set([F("George Washington"), F("Tadeusz Kościuszko")]) == names

def test_names_with_manager():
    m = parse_match("[Tadeusz Kościuszko, George Washington; Samuel Adams]")
    names = metadata.names_in_match(m)
    assert set([F("George Washington"), F("Tadeusz Kościuszko"), M("Samuel Adams")]) == names

def test_names_with_adhoc_teams():
    m = parse_match("""
                    - 'Tadeusz Kościuszko, Kazimierz Pułaski'
                    - 'Bill Clinton, Hillary Clinton'
                    """)
    names = metadata.names_in_match(m)
    assert set([F("Kazimierz Pułaski"), F("Tadeusz Kościuszko"), F("Bill Clinton"), F("Hillary Clinton")]) == names

def test_all_names_with_adhoc_teams():
    m = parse_match("""
                    - 'Tadeusz Kościuszko, Kazimierz Pułaski'
                    - 'Bill Clinton, Hillary Clinton'
                    """)
    # Testing Card/Match
    names = list(m.all_names())
    # Note it's a list - we're expecting names in this order
    expected = [
        F("Tadeusz Kościuszko"),
        F("Kazimierz Pułaski"),
        F("Bill Clinton"),
        F("Hillary Clinton")
    ]
    assert expected == names

def test_names_with_options():
    m = parse_match("""
                    - Abe Lincoln
                    - Bill Clinton
                    - s: Best President Match
                    """)
    # Testing Card/Match, not metadata
    assert {"s": "Best President Match"} == m.options
    names = metadata.names_in_match(m)
    assert set([F("Abe Lincoln"), F("Bill Clinton")]) == names

def test_names_with_exclusions():
    m = parse_match("""
                    - Bill Clinton
                    - George Bush
                    - Barack Obama
                    - Joe Biden
                    - x: [1]
                    """)
    names = metadata.names_in_match(m)
    expected = set([
        F("Joe Biden"),
        F("George Bush"),
        F("Barack Obama")
    ])
    assert expected == names