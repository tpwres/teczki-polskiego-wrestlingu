from pathlib import Path
from linters.base import LintError, Doc, Linter
from errors import FileError, FileWarning, LintWarning
from card import CardParseError
from utils import extract_front_matter, strip_blocks
from md_utils import find_links
from page import EventPage
from dataclasses import dataclass
import re
import datetime
import tomllib
import yaml, yaml.scanner
from mistletoe import Document
from mistletoe.markdown_renderer import MarkdownRenderer
from mistletoe.span_token import Link
from typing import Tuple, Generator

def find_bad_links(text: str) -> Generator[Tuple[Link, int, str], None, None]:
    """Similar to find_links but yields only links with bad targets."""
    doc = Document(text)
    for link, linenum in find_links(doc):
        match link:
            case Link(target=target) if not valid_link_target(target):
                yield (link, linenum, bad_link_reason(target))

def valid_content_link(content_path: str|Path) -> bool:
    """Check if file named by content_path exists"""
    content_root = Path.cwd() / "content"
    target = content_root / content_path

    return target.exists()

def valid_link_target(target: str) -> bool:
    """Basic link validation. For internal links, checks if target exists."""
    if target.startswith('@/'):
        target, hash, fragment = target.partition('#')
        return valid_content_link(target[2:])
    elif target.startswith('http://'):
        return False # Outgoing links must be https
    else:
        return True

def bad_link_reason(target: str) -> str:
    """Basic link validation. For internal links, checks if target exists."""
    if target.startswith('@/'):
        target, _, _= target.partition('#')
        return f"File `{target[2:]}` not found"
    elif target.startswith('http://'):
        return "Insecure http links not allowed"
    else:
        return 'OK'

markdown_renderer = MarkdownRenderer()

def rerender_link(link: Link) -> str:
    """Converts a Link back into markdown."""
    return "".join(markdown_renderer.render(link)).rstrip()

F = FileError
W = FileWarning

class WellFormedEventLinter(Linter):
    """
    A well formed event file has:
    ✅ filename matching proscribed pattern: yyyy-mm-dd-orgs-event-name.md
    ✅ parent dir must be an org name, and repeated in orgs
    - a valid frontmatter block
      ✅ with mandatory fields: title
      ✅ template must be event_page or other whitelisted ones
      - taxonomies, if present, must be valid
        ✅ values for chronology must be in chrono_root
        ✅ venue must have exactly one element, and matching an article in v/
      - gallery items, if present, must be well-formed
        ✅ mandatory attributes: path, caption, source
        ✅ markdown links in caption are valid
        - if possible, validate path exists
        - if path exists, validate file size is within limit
    - a card block or a {{ skip_card() }} annotation
      ✅ that is valid yaml
      ✅ error if card is empty
      ✅ warning if no credits entry
      ✅ each talent link is valid
      - links in c: and n: options are valid
    - mandatory sections: References
    ✅ all internal links must be valid
    """
    def __init__(self, config, linter_options):
        self.messages = []
        self.config = config
        self.linter_options = linter_options
        self.load_taxonomies()

    def handles(self, path: Path) -> bool:
        # Only process event files
        return path.match('????-??-??-*.md')

    def reset(self):
        self.target_path = None
        self.messages = []

    def lint(self, document: Doc):
        path = document.pathname()
        if not path.exists():
            return self.messages

        self.target_path = path
        if not self.option_enabled('wfe:skip-filename-check'):
            self.check_filename(path)

        try:
            self.content_root = [p for p in path.parents if p.stem == 'content'].pop()
        except IndexError:
            self.content_root = Path.cwd() / 'content'

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
            self.error("Path does not adhere to naming scheme YYYY-MM-DD-ORGS-Event-Name.md")
            return

        y, m, d = int(fc['year']), int(fc['month']), int(fc['day'])
        if y <= 1900:
            self.error(f"Year {y} is before 1900")
        if not 1 <= m <= 12:
            self.error(f"Month {m} is not between 1 and 12")
        if not 1 <= d <= 31:
            self.error(f"Day of month {d} is not between 1 and 31")

        try:
            datetime.date(y, m, d)
        except ValueError:
            self.error(f"Date {fc['year']}-{fc['month']}-{fc['day']} is invalid.")

        orgs = fc['orgs'].split('_')
        if not orgs:
            # Redundant, as it will fail the naming scheme check first, which returns early
            self.error(f"Filename must contain organization or organizations")

        dir = str(path.parent.name)
        if dir not in orgs:
            self.error(f"File is marked with orgs `{','.join(orgs)}` but is not located in any of their directories")

    def check_frontmatter(self, path, text):
        matter = None
        try:
            matter = extract_front_matter(text)
        except ValueError:
            self.error("Could not find proper front matter block surrounded by `+++`")

        if not matter:
            self.error("Front matter block is empty")
            return

        try:
            fmc = tomllib.loads(matter)
        except tomllib.TOMLDecodeError as err:
            self.error(f"Invalid TOML in front matter: {err}")
            return

        title = fmc.get('title')
        if not title:
            self.error("Missing title in frontmatter")

        template = fmc.get('template')
        if template != 'event_page.html':
            self.error("Event page must use the `event_page.html` template")

        taxonomies = fmc.get('taxonomies')
        if not taxonomies:
            self.warning("Event page should have taxonomies. Recommended taxonomies are `chrono` and `venue`")
        else:
            self.check_taxonomies(path, taxonomies)

        extra = fmc.get('extra')
        if not extra:
            return

        gallery = extra.get('gallery')
        if gallery:
            manifest = gallery.get('manifest', None)
            if manifest:
                manifest_path = Path(manifest.replace('@', str(self.content_root)))
                gallery = tomllib.load(manifest_path.open('rb'))
            self.check_gallery(path, gallery)

    def check_taxonomies(self, path, doc_taxonomies):
        keys = set(doc_taxonomies.keys())
        unknown = keys - set(self.taxonomies.keys())
        if unknown:
            self.error(f"Unknown taxonomies `{','.join(unknown)}`")

        chrono = doc_taxonomies.get('chronology')
        if chrono:
            unknown = set(chrono) - self.chronologies
            if unknown:
                self.error(f"Unknown chronology keys `{','.join(unknown)}`")

        venues = doc_taxonomies.get('venue')
        if venues:
            if len(venues) > 1:
                self.warning(f"Venues taxonomy should only have one entry, but has {len(venues)}")
            unknown = set(venues) - self.venues
            if unknown:
                self.warning(f"Unknown venue keys `{','.join(unknown)}`")

    def check_gallery(self, path, gallery):
        for key, val in gallery.items():
            pp, caption, source = val.get('path'), val.get('caption'), val.get('source')
            if not pp:
                self.error(f"Gallery item {key} is missing path")
            else:
                self.verify_gallery_path_exists(path, pp)
            if not source:
                self.error(f"Gallery item {key} is missing source annotation")
            if not caption:
                self.error(f"Gallery item {key} is missing caption")
            else:
                for link, _, reason in find_bad_links(caption):
                    self.error(
                        f"Malformed link {rerender_link(link)} in caption of gallery item `{key}`. {reason}"
                    )


    def verify_gallery_path_exists(self, path, image_path):
        # TODO
        pass

    def check_card(self, path, text):
        if '{{ skip_card() }}' in text:
            self.warning("Card marked as skipped")
            return

        try:
            page = EventPage(path, verbose=False)
        except yaml.scanner.ScannerError as e:
            # TODO: These errors show very wrong line numbers
            # Aren't these swallowed into CPEs below?
            msg = str(e).replace('\n', ' ')
            self.error(f"Error while parsing card: {msg}")
            return
        except CardParseError as cpe:
            msg = str(cpe).replace('\n', ' ')
            self.error(f"Parse error: {msg}")
            return
        except KeyError as e:
            self.error(f"Missing required key {e}")
            return
        except ValueError as e:
            self.error(f"Malformed card, did not parse valid matches. {e}")
            return

        card = page.card

        if not card.matches:
            self.error("Card missing or no matches listed")
            return

        if not card.crew:
            self.warning("Credits section missing in card")

        # TODO: line numbers - Card doesn't track them yet
        for num, mm in enumerate(card.matches, 1):
            for item in mm.line:
                # Line contains both participants and options
                if not isinstance(item, str): continue
                for link, _, reason in find_bad_links(item):
                    self.error(f"Malformed link `{rerender_link(link)}` in match {num} participants. {reason}")

            if championship := mm.options.get('c'):
                doc = Document(championship)
                for link, _, reason in find_bad_links(championship):
                    self.error(f"Malformed link `{rerender_link(link)}` in match {num} championship. {reason}")

            if notes := mm.options.get('n'):
                text = "".join(notes) if isinstance(notes, list) else notes
                for link, _, reason in find_bad_links(text):
                    self.error(f"Malformed link `{rerender_link(link)}` in match {num} notes. {reason}")

    def check_body_links(self, path, text):
        plain_text = strip_blocks(text)

        for link, linenum, reason in find_bad_links(plain_text):
            self.error(f"Malformed link `{rerender_link(link)}` near line {linenum}. {reason}")

    def load_taxonomies(self):
        taxonomies = {o['name']: o for o in self.config['taxonomies']}
        self.taxonomies = taxonomies

        custom_chrono = self.config['extra']['chronology'].keys()
        path_chronos = [p.stem for p in Path('content/o').glob('*.md') if p.stem != '_index']
        self.chronologies = set([*custom_chrono, *path_chronos])

        self.venues = set([p.stem for p in Path('content/v').glob('*.md') if p.stem != '_index'])

    def option_enabled(self, code):
        value = self.linter_options.get(code, False)
        return value
