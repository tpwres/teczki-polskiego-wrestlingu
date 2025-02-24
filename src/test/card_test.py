
from card import parse_group, Fighter, Manager

def test_commas():
    result = parse_group('Biesiad, Goblin, Axel Fox')
    assert len(result) == 3
    assert all(isinstance(p, Fighter) for p in result)

def test_with_and_semi_are_equivalent():
    result1 = parse_group('Biesiad, Goblin; Axel Fox')
    result2 = parse_group('Biesiad, Goblin w/ Axel Fox')
    assert result2 == result1
    biesiad, goblin, fox = result1
    assert isinstance(biesiad, Fighter)
    assert isinstance(goblin, Fighter)
    assert isinstance(fox, Manager)

def test_ampersand_manager():
    result1 = parse_group('Biesiad w/ Goblin & Axel Fox')
    biesiad, goblin, fox = result1
    assert isinstance(biesiad, Fighter)
    assert isinstance(goblin, Manager)
    assert isinstance(fox, Manager)

def test_ampersand_fighter():
    result1 = parse_group('Biesiad & Goblin w/ Axel Fox')
    biesiad, goblin, fox = result1
    assert isinstance(biesiad, Fighter)
    assert isinstance(goblin, Fighter)
    assert isinstance(fox, Manager)

def test_ampersand_madness():
    result1 = parse_group('Biesiad, Sambor & Goblin w/ Axel Fox & Johnny Blade')
    biesiad, sambor, goblin, fox, johnny = result1
    assert isinstance(biesiad, Fighter)
    assert isinstance(sambor, Fighter)
    assert isinstance(goblin, Fighter)
    assert isinstance(fox, Manager)
    assert isinstance(johnny, Manager)

def test_with_and_linked_names():
    result1 = parse_group('[Biesiad](@/w/biesiad.md) w/ [Goblin](@/w/goblin.md) & [Axel Fox](@/w/axel-fox.md)')
    biesiad, goblin, fox = result1
    print(biesiad)
    assert isinstance(biesiad, Fighter) and biesiad.link == '@/w/biesiad.md'
    assert isinstance(goblin, Manager) and goblin.link == '@/w/goblin.md'
    assert isinstance(fox, Manager) and fox.link == '@/w/axel-fox.md'

