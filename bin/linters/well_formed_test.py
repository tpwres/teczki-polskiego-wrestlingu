from well_formed_event import WellFormedEventLinter, FileError
from base import LintError, FileBackedDoc
from pathlib import Path
from textwrap import dedent
import pytest
from pytest import fail

@pytest.fixture
def config_toml():
    return dict(
        taxonomies=[],
        extra=dict(
            chronology={}
        )
    )

@pytest.fixture
def valid_header():
    return dedent('''
        +++
        title = "Event Name"
        template = "event_page.html"
        +++
    ''')

def assert_exact_message(messages: list[FileError]|None, text: str):
    if not messages:
        fail("No messages passed to assert_exact_message")
    assert any(m.text == text for m in messages), f"Could not find text `{text}` in messages"

def assert_message(messages: list[FileError]|None, text: str):
    if not messages:
        fail("No messages passed to assert_message")
    assert any(text in m.text for m in messages), f"Could not find text `{text}` in messages"

def refute_exact_message(messages: list[FileError]|None, text: str):
    if not messages:
        fail("No messages passed to refute_exact_message")

    if any(m.text == text for m in messages):
        fail(f"Text `{text}` was found in messages")

def refute_message(messages: list[FileError]|None, text: str):
    if not messages:
        fail("No messages passed to refute_message")

    if any(text in m.text for m in messages):
        fail(f"Text `{text}` was found in messages")

def test_very_bad_filename(tmp_path, config_toml):
    path = tmp_path / 'event-name.md'
    path.touch()

    linter = WellFormedEventLinter(config_toml)
    doc = FileBackedDoc(path)

    messages = linter.lint(doc)
    assert_exact_message(messages, "Path does not adhere to naming scheme YYYY-MM-DD-ORGS-Event-Name.md")

def test_filename_without_date(tmp_path, config_toml):
    path = tmp_path / 'mzw-event-name.md'
    path.touch()

    linter = WellFormedEventLinter(config_toml)
    doc = FileBackedDoc(path)

    messages = linter.lint(doc)
    assert_exact_message(messages, "Path does not adhere to naming scheme YYYY-MM-DD-ORGS-Event-Name.md")

def test_filename_with_invalid_day(tmp_path, config_toml):
    path = tmp_path / '2024-12-35-mzw-event-name.md'
    path.touch()

    linter = WellFormedEventLinter(config_toml)
    doc = FileBackedDoc(path)

    messages = linter.lint(doc)
    assert_exact_message(messages, "Day of month 35 is not between 1 and 31")

def test_filename_with_invalid_month(tmp_path, config_toml):
    path = tmp_path / '2024-13-31-mzw-event-name.md'
    path.touch()

    linter = WellFormedEventLinter(config_toml)
    doc = FileBackedDoc(path)

    messages = linter.lint(doc)
    assert_exact_message(messages, "Month 13 is not between 1 and 12")

def test_filename_with_invalid_year_too_early(tmp_path, config_toml):
    path = tmp_path / '1899-12-31-mzw-event-name.md'
    path.touch()

    linter = WellFormedEventLinter(config_toml)
    doc = FileBackedDoc(path)

    messages = linter.lint(doc)
    assert_exact_message(messages, "Year 1899 is before 1900")

def test_filename_with_invalid_date(tmp_path, config_toml):
    path = tmp_path / '2023-02-29-mzw-event-name.md'
    path.touch()

    linter = WellFormedEventLinter(config_toml)
    doc = FileBackedDoc(path)

    messages = linter.lint(doc)
    assert_exact_message(messages, "Date 2023-02-29 is invalid.")

def test_filename_must_have_org(tmp_path, config_toml):
    path = tmp_path / '2023-02-28--event-name.md'
    path.touch()

    linter = WellFormedEventLinter(config_toml)
    doc = FileBackedDoc(path)

    messages = linter.lint(doc)
    assert_exact_message(messages, "Path does not adhere to naming scheme YYYY-MM-DD-ORGS-Event-Name.md")

    path = (tmp_path / '2023-02-28-xwp-event-name.md')
    path.touch()

    linter = WellFormedEventLinter(config_toml)
    doc = FileBackedDoc(path)

    messages = linter.lint(doc)
    refute_exact_message(messages, "Path does not adhere to naming scheme YYYY-MM-DD-ORGS-Event-Name.md")
    refute_exact_message(messages, "Filename must contain organization or organizations")

def test_filename_must_be_in_org_dir(tmp_path, config_toml):
    path = tmp_path / '2023-02-28-mzw-event-name.md'
    path.touch()

    linter = WellFormedEventLinter(config_toml)
    doc = FileBackedDoc(path)

    messages = linter.lint(doc)
    assert_exact_message(messages, "File is marked with orgs `mzw` but is not located in any of their directories")

def test_filename_in_org_dir(tmp_path, config_toml):
    (tmp_path / 'mzw').mkdir()
    path = tmp_path / 'mzw' / '2023-02-28-mzw-event-name.md'
    path.touch()

    linter = WellFormedEventLinter(config_toml)
    doc = FileBackedDoc(path)

    messages = linter.lint(doc)
    refute_exact_message(messages, "File is marked with orgs `mzw` but is not located in any of their directories")

def test_missing_frontmatter(tmp_path, config_toml):
    path = tmp_path / '2023-02-28-mzw-event-name.md'
    path.touch()

    linter = WellFormedEventLinter(config_toml)
    doc = FileBackedDoc(path)

    messages = linter.lint(doc)
    assert_exact_message(messages, "Could not find proper front matter block surrounded by `+++`")

def test_empty_frontmatter(tmp_path, config_toml):
    path = tmp_path / '2023-02-28-mzw-event-name.md'
    with path.open('w') as fp:
        fp.write('+++\n+++')

    linter = WellFormedEventLinter(config_toml)
    doc = FileBackedDoc(path)

    messages = linter.lint(doc)
    refute_exact_message(messages, "Could not find proper front matter block surrounded by `+++`")
    assert_exact_message(messages, "Front matter block is empty")
    assert_exact_message(messages, "Missing required key 'title'")

def test_bad_toml_frontmatter(tmp_path, config_toml):
    path = tmp_path / '2023-02-28-mzw-event-name.md'
    with path.open('w') as fp:
        fp.write(dedent('''
        +++
        title = "Event Name"
        moo = {1 = }
        +++
        '''))

    linter = WellFormedEventLinter(config_toml)
    doc = FileBackedDoc(path)

    messages = linter.lint(doc)
    assert_exact_message(messages, "Invalid TOML in front matter: Invalid value (at line 2, column 12)")

def test_missing_title_in_frontmatter(tmp_path, config_toml):
    path = tmp_path / '2023-02-28-mzw-event-name.md'
    with path.open('w') as fp:
        fp.write(dedent('''
        +++
        foo = "bar"
        +++
        '''))

    linter = WellFormedEventLinter(config_toml)
    doc = FileBackedDoc(path)

    messages = linter.lint(doc)
    assert_exact_message(messages, "Missing title in frontmatter")
    assert_exact_message(messages, "Event page must use the `event_page.html` template")

def test_bad_template_in_frontmatter(tmp_path, config_toml):
    path = tmp_path / '2023-02-28-mzw-event-name.md'
    with path.open('w') as fp:
        fp.write(dedent('''
        +++
        title = "Event Name"
        template = "article.html"
        +++
        '''))

    linter = WellFormedEventLinter(config_toml)
    doc = FileBackedDoc(path)

    messages = linter.lint(doc)
    refute_exact_message(messages, "Missing title in frontmatter")
    assert_exact_message(messages, "Event page must use the `event_page.html` template")

def test_missing_taxonomies_in_frontmatter(tmp_path, config_toml, valid_header):
    path = tmp_path / '2023-02-28-mzw-event-name.md'
    with path.open('w') as fp:
        fp.write(valid_header)

    linter = WellFormedEventLinter(config_toml)
    doc = FileBackedDoc(path)

    messages = linter.lint(doc)
    refute_exact_message(messages, "Missing title in frontmatter")
    refute_exact_message(messages, "Event page must use the `event_page.html` template")
    assert_exact_message(messages, "Event page should have taxonomies. Recommended taxonomies are `chrono` and `venue`")

def test_bad_taxonomies(tmp_path, config_toml):
    path = tmp_path / '2023-02-28-mzw-event-name.md'
    with path.open('w') as fp:
        fp.write(dedent('''
        +++
        title = "Event Name"
        template = "event_page.html"
        [taxonomies]
        foo = ["bar"]
        chronology = ["xpw"]
        venue = ["pensjonat-bekas"]
        +++
        '''))

    config_toml['taxonomies'].append(dict(name = "chronology"))
    config_toml['taxonomies'].append(dict(name = "venue"))
    linter = WellFormedEventLinter(config_toml)
    doc = FileBackedDoc(path)

    messages = linter.lint(doc)
    assert_exact_message(messages, "Unknown taxonomies `foo`")
    assert_exact_message(messages, "Unknown chronology keys `xpw`")
    assert_exact_message(messages, "Unknown venue keys `pensjonat-bekas`")

def test_accepts_chronologies(tmp_path, config_toml):
    path = tmp_path / '2023-02-28-mzw-event-name.md'
    with path.open('w') as fp:
        fp.write(dedent('''
        +++
        title = "Event Name"
        template = "event_page.html"
        [taxonomies]
        chronology = ["xpw", "mazury"]
        venue = ["pensjonat-bekas"]
        +++
        '''))

    config_toml['taxonomies'].append(dict(name = "chronology"))
    config_toml['taxonomies'].append(dict(name = "venue"))
    linter = WellFormedEventLinter(config_toml)
    # Override value set from file structure
    linter.chronologies = {'mazury', 'xpw'}
    linter.venues = {'pensjonat-bekas'}

    doc = FileBackedDoc(path)
    messages = linter.lint(doc)
    refute_exact_message(messages, "Unknown chronology keys `xpw`")
    refute_exact_message(messages, "Unknown chronology keys `mazury`")
    refute_exact_message(messages, "Unknown venue keys `pensjonat-bekas`")

def test_malformed_gallery(tmp_path, config_toml):
    path = tmp_path / '2023-02-28-mzw-event-name.md'
    with path.open('w') as fp:
        fp.write(dedent('''
        +++
        title = "Event Name"
        template = "event_page.html"
        [extra.gallery]
        1 = { caption = "Only Caption" }
        2 = { path = "1.jpg", source = "Source" }
        +++
        '''))

    linter = WellFormedEventLinter(config_toml)
    doc = FileBackedDoc(path)

    messages = linter.lint(doc)
    assert_exact_message(messages, "Gallery item 1 is missing path")
    assert_exact_message(messages, "Gallery item 1 is missing source annotation")
    refute_exact_message(messages, "Gallery item 1 is missing caption")
    refute_exact_message(messages, "Gallery item 2 is missing path")
    refute_exact_message(messages, "Gallery item 2 is missing source annotation")
    assert_exact_message(messages, "Gallery item 2 is missing caption")

def test_missing_card(tmp_path, config_toml, valid_header):
    path = tmp_path / '2023-02-28-mzw-event-name.md'
    with path.open('w') as fp:
        fp.write(valid_header)
        # Header and nothing else

    linter = WellFormedEventLinter(config_toml)
    doc = FileBackedDoc(path)

    messages = linter.lint(doc)
    assert_exact_message(messages, "Card missing or no matches listed")

def test_skip_card(tmp_path, config_toml, valid_header):
    path = tmp_path / '2023-02-28-mzw-event-name.md'
    with path.open('w') as fp:
        fp.write(valid_header)
        fp.write('{{ skip_card() }}\n')

    linter = WellFormedEventLinter(config_toml)
    doc = FileBackedDoc(path)

    messages = linter.lint(doc)
    refute_exact_message(messages, "Card missing or no matches listed")
    assert_exact_message(messages, "Card marked as skipped")

def test_unclosed_card(tmp_path, config_toml, valid_header):
    path = tmp_path / '2023-02-28-mzw-event-name.md'
    with path.open('w') as fp:
        fp.write(valid_header)
        fp.write(dedent('''
        {% card() %}
        - - Undertaker
        - Randy Savage
        '''))

    linter = WellFormedEventLinter(config_toml)
    doc = FileBackedDoc(path)

    messages = linter.lint(doc)
    assert_exact_message(messages, "Malformed card, did not parse valid matches")
    refute_exact_message(messages, "Card marked as skipped")

def test_malformed_card(tmp_path, config_toml, valid_header):
    path = tmp_path / '2023-02-28-mzw-event-name.md'
    with path.open('w') as fp:
        fp.write(valid_header)
        fp.write(dedent('''
        {% card() %}
        - [Undertaker](@/w/undertaker.md)
        {% end %}
        '''))

    linter = WellFormedEventLinter(config_toml)
    doc = FileBackedDoc(path)

    messages = linter.lint(doc)
    assert_message(messages, "Error: expected <block end>, but found '<scalar>' while parsing a block collection")

def test_no_credits(tmp_path, config_toml, valid_header):
    path = tmp_path / '2023-02-28-mzw-event-name.md'
    with path.open('w') as fp:
        fp.write(valid_header)
        fp.write(dedent('''
        {% card() %}
        - ['[Undertaker](@/w/undertaker.md)', 'Doink']
        {% end %}
        '''))

    linter = WellFormedEventLinter(config_toml)
    doc = FileBackedDoc(path)

    messages = linter.lint(doc)
    refute_exact_message(messages, "Card missing or no matches listed")
    refute_exact_message(messages, "Card marked as skipped")
    refute_exact_message(messages, "Malformed card, did not parse valid matches")
    assert_exact_message(messages, "Credits section missing in card")
    assert_exact_message(messages, "Malformed link `[Underfaker](@/w/underfaker.md)` in match 1")

