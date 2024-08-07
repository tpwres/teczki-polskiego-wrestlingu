from pathlib import Path
from linters.base import LintError, Doc
from card import CardParseError
from utils import extract_front_matter
from page import Page
from dataclasses import dataclass
import re
import datetime
import tomllib
import yaml, yaml.scanner
from mistletoe import Document
from mistletoe.ast_renderer import get_ast
from typing import Tuple, Generator

@dataclass
class FileError(LintError):
    path: Path
    text: str

    def message(self, file_root: Path):
        return f'[{self.path.relative_to(file_root)}] {self.text}'

    def supports_auto(self):
        return False

class LintWarning(LintError): pass

@dataclass
class FileWarning(LintWarning):
    path: Path
    text: str

    def message(self, file_root: Path):
        return f'[{self.path.relative_to(file_root)}] Warning: {self.text}'

    def supports_auto(self):
        return False

def strip_blocks(text: str) -> str:
    frontmatter_re = re.compile(r'''
      ^[+]{3}$ # Frontmatter delimiter: three pluses on a standalone line
      (?P<frontmatter>(?:.|\n)*) # Frontmatter content
      ^[+]{3}$ # Another delimiter
    ''', re.VERBOSE | re.MULTILINE)
    block_re = r"^\{%\s+(?P<keyword>\w+)\([^)]*\)\s+%\}$(?P<content>(?:\n|.)*)^\{%\s+end\s+%\}$", re.MULTILINE
    block_re = re.compile(r'''
      ^\{%\s+                # Opening {% and whitespace
      (?P<keyword>\w+)       # keyword (usually card)
      \([^)]*\)              # Open parentheses, any content, closing parentheses
      \s+                    # Followed by whitespace
      %\}$                   # Closing %}
      (?P<content>(?:\n|.)*) # Block content
      ^\{%\s+                # Opening {% and whitespace
      end\s+                 # End keyword, whitespace
      %\}$                   # Closing %}
    ''', re.VERBOSE | re.MULTILINE)
    passthrough_keywords = {'timeline'}

    def replace_block(matchobj):
        if matchobj.group('keyword') in passthrough_keywords:
            return f"\n{matchobj.group('content')}\n"
        else:
            return "\n" * matchobj.group('content').count("\n")

    body = frontmatter_re.sub(lambda matchobj: "\n" * matchobj.group('frontmatter').count("\n"), text)
    return block_re.sub(replace_block, body)

def find_links(element: dict, line_number:int=0) -> Generator[Tuple[dict, int], None, None]:
    """Walk the AST recursively, yielding any links found."""

    if 'line_number' in element:
        line_number = element['line_number']

    if element['type'] == 'Link':
        yield (element, line_number)
    elif 'children' in element:
        for child in element['children']:
            yield from find_links(child, line_number)

def valid_content_link(content_path):
    """Check if file named by content_path exists"""
    content_root = Path.cwd() / "content"
    target = content_root / content_path

    return target.exists()

def valid_link_target(target):
    if target.startswith('@/'):
        return valid_content_link(target[2:])
    elif target.startswith('http://'):
        return False # Outgoing links must be https
    else:
        return True

F = FileError
W = FileWarning

class WellFormedEventLinter:
    """
    A well formed event file has:
    - filename matching proscribed pattern: yyyy-mm-dd-orgs-event-name.md
      - parent dir must be an org name, and repeated in orgs
    - a valid frontmatter block
      - with mandatory fields: title
      - template must be event_page or other whitelisted ones
      - taxonomies, if present, must be valid
        - values for chronology must be in chrono_root
        - venue must have exactly one element, and matching an article in v/
      - gallery items, if present, must be well-formed
        - mandatory attributes: path, caption, source
        - if possible, validate path exists
        - if path exists, validate file size is within limit
    - a card block or a {{ skip_card() }} annotation
      - that is valid yaml
      - error if card is empty
      - warning if no credits entry
    - mandatory sections: References
    - all internal links must be valid
    """
    def __init__(self, config):
        self.messages = []
        self.config = config
        self.load_taxonomies()

    def lint(self, document: Doc):
        path = document.pathname()
        if not path.exists():
            return self.messages

        self.target_path = path
        self.check_filename(path)

        with document.open() as fp:
            text = fp.read()
            self.check_frontmatter(path, text)

            self.check_card(path, text)

            self.check_body_links(path, text)
            #self.check_sections(text)

        return self.messages

    def error(self, err: LintError|str):
        match err:
            case LintError() as lint_err:
                self.messages.append(lint_err)
            case str(text):
                self.messages.append(F(self.target_path, text))

    def warning(self, warning: LintWarning|str):
        match warning:
            case LintWarning() as lint_warn:
                self.messages.append(lint_warn)
            case str(text):
                self.messages.append(W(self.target_path, text))

    def check_filename(self, path):
        fc = re.match(r'''
            ^
            (?P<year>\d{4})-(?P<month>\d{2})-(?P<day>\d{2})
            -(?P<orgs>[^-]+)
            -(?P<title>.*)
            \.md
            $
        ''', path.name, flags=re.VERBOSE)
        if not fc:
            self.error(F(path, "Path does not adhere to naming scheme YYYY-MM-DD-ORGS-Event-Name.md"))
            return

        y, m, d = int(fc['year']), int(fc['month']), int(fc['day'])
        if y <= 1900:
            self.error(F(path, f"Year {y} is before 1900"))
        if not 1 <= m <= 12:
            self.error(F(path, f"Month {m} is not between 1 and 12"))
        if not 1 <= d <= 31:
            self.error(F(path, f"Day of month {d} is not between 1 and 31"))

        try:
            datetime.date(y, m, d)
        except ValueError:
            self.error(F(path, f"Date {fc['year']}-{fc['month']}-{fc['day']} is invalid."))

        orgs = fc['orgs'].split('_')
        if not orgs:
            # Redundant, as it will fail the naming scheme check first, which returns early
            self.error(F(path, f"Filename must contain organization or organizations"))

        dir = str(path.parent.name)
        if dir not in orgs:
            self.error(F(path, f"File is marked with orgs `{','.join(orgs)}` but is not located in any of their directories"))

    def check_frontmatter(self, path, text):
        matter = None
        try:
            matter = extract_front_matter(text)
        except ValueError:
            self.error(F(path, "Could not find proper front matter block surrounded by `+++`"))

        if not matter:
            self.error(F(path, "Front matter block is empty"))
            return

        try:
            fmc = tomllib.loads(matter)
        except tomllib.TOMLDecodeError as err:
            self.error(F(path, f"Invalid TOML in front matter: {err}"))
            return

        title = fmc.get('title')
        if not title:
            self.error(F(path, "Missing title in frontmatter"))

        template = fmc.get('template')
        if template != 'event_page.html':
            self.error(F(path, "Event page must use the `event_page.html` template"))

        taxonomies = fmc.get('taxonomies')
        if not taxonomies:
            self.warning(F(path, "Event page should have taxonomies. Recommended taxonomies are `chrono` and `venue`"))
        else:
            self.check_taxonomies(path, taxonomies)

        extra = fmc.get('extra')
        if not extra:
            return

        gallery = extra.get('gallery')
        if gallery:
            self.check_gallery(path, gallery)

    def check_taxonomies(self, path, doc_taxonomies):
        keys = set(doc_taxonomies.keys())
        unknown = keys - set(self.taxonomies.keys())
        if unknown:
            self.error(F(path, f"Unknown taxonomies `{','.join(unknown)}`"))

        chrono = doc_taxonomies.get('chronology')
        if chrono:
            unknown = set(chrono) - self.chronologies
            if unknown:
                self.error(F(path, f"Unknown chronology keys `{','.join(unknown)}`"))

        venues = doc_taxonomies.get('venue')
        if venues:
            if len(venues) > 1:
                self.warning(F(path, f"Venues taxonomy should only have one entry, but has {len(venues)}"))
            unknown = set(venues) - self.venues
            if unknown:
                self.warning(F(path, f"Unknown venue keys `{','.join(unknown)}`"))

    def check_gallery(self, path, gallery):
        for key, val in gallery.items():
            pp, caption, source = val.get('path'), val.get('caption'), val.get('source')
            if not pp:
                self.error(F(path, f"Gallery item {key} is missing path"))
            else:
                self.verify_gallery_path_exists(path, pp)
            if not caption:
                self.error(F(path, f"Gallery item {key} is missing caption"))
            if not source:
                self.error(F(path, f"Gallery item {key} is missing source annotation"))

    def verify_gallery_path_exists(self, path, image_path):
        # TODO
        pass

    def check_card(self, path, text):
        if '{{ skip_card() }}' in text:
            self.warning(F(path, "Card marked as skipped"))
            return

        try:
            page = Page(path, verbose=False)
        except yaml.scanner.ScannerError as e:
            # TODO: These errors show very wrong line numbers
            # Aren't these swallowed into CPEs below?
            self.error(F(path, f"Error while parsing card: {str(e).replace('\n', ' ')}"))
            return
        except CardParseError as cpe:
            self.error(F(path, f"Parse error: {str(cpe).replace('\n', '')}"))
            return
        except KeyError as e:
            self.error(F(path, f"Missing required key {e}"))
            return
        except ValueError:
            self.error(F(path, f"Malformed card, did not parse valid matches"))
            return

        card = page.card

        if not card.matches:
            self.error(F(path, "Card missing or no matches listed"))
            return

        if not card.crew:
            self.warning(F(path, "Credits section missing in card"))


    def check_body_links(self, path, text):
        plain_text = strip_blocks(text)
        doc = Document(plain_text)

        for (link, linenum) in find_links(get_ast(doc)):
            match link:
                case {'target': target} if valid_link_target(target):
                    pass
                case {'target': target, 'title': title}:
                    self.error(F(path, f"Malformed link target ({target}) near line {linenum}"))

    def load_taxonomies(self):
        taxonomies = {o['name']: o for o in self.config['taxonomies']}
        self.taxonomies = taxonomies

        custom_chrono = self.config['extra']['chronology'].keys()
        path_chronos = [p.stem for p in Path('content/o').glob('*.md') if p.stem != '_index']
        self.chronologies = set([*custom_chrono, *path_chronos])

        self.venues = set([p.stem for p in Path('content/v').glob('*.md') if p.stem != '_index'])
