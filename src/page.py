import re
from datetime import datetime, date
from pathlib import Path
from card import Card
from typing import Iterable, Optional, cast
from io import TextIOBase
from warnings import deprecated
from rich_doc import RichDoc
from sink import ExplosiveSink

FrontMatterPrimitive = str | int | float
FrontMatterValue = FrontMatterPrimitive | list[FrontMatterPrimitive] | dict[str, FrontMatterPrimitive]
FrontMatter = dict[str, FrontMatterValue]

class Page:
    def __init__(self, doc: RichDoc, verbose: bool = True):
        self.doc = doc

    @property
    def front_matter(self):
        return self.doc.front_matter

    @property
    def title(self): return self.front_matter['title']

    @property
    def path(self): return self.doc.path

    def __repr__(self):
        return f"<{self.__class__.__name__}({self.doc.path})>"

class EventPage(Page):
    event_date: date
    orgs: list[str]

    date_org_re = re.compile(r'^(?P<date>\d{4}-\d\d-\d\d)-(?P<orgs>[^-]+)')

    @property
    def card(self) -> Optional[Card]:
        card_section = self.doc.card_section
        if not card_section:
            return None

        return Card(card_section, self.doc)

    def __init__(self, doc: RichDoc, verbose: bool = True):
        super().__init__(doc, verbose)

        path = doc.path
        match EventPage.date_org_re.match(path.stem):
            case re.Match() as m:
                ymd = m.group('date')
                self.event_date = datetime.strptime(ymd, '%Y-%m-%d').date()
                self.orgs = m.group('orgs').split('_')

    def __repr__(self):
        return f"<EventPage({self.doc.path}) date={self.event_date} orgs={self.orgs}>"


@deprecated("Replace with RichDoc or rework")
class OrgPage(Page):
    pass

@deprecated("Replace with RichDoc or rework")
class VenuePage(Page):
    pass

class TalentPage(Page):
    def __repr__(self):
        title = self.front_matter.get('title', None)
        return f"<TalentPage({self.path}) name={title!r}>"

class Article(Page):
    pass

def page(doc: RichDoc, verbose: bool = False) -> Page:
    """Returns a subclass of Page, based on what's the most appropriate
    for the path given."""
    path = doc.path
    if Path('content/e') in path.parents or EventPage.date_org_re.match(path.stem):
        return EventPage(doc, verbose)
    elif path.match('o/*.md'):
        return OrgPage(doc, verbose)
    elif path.match('w/*.md'):
        return TalentPage(doc, verbose)
    elif path.match('v/*.md'):
        return VenuePage(doc, verbose)
    else:
        return Article(doc, verbose)

def default_sink():
    return ExplosiveSink()

def all_talent_pages(root: Optional[Path]=None) -> Iterable[TalentPage]:
    """Walk the files and produce all talent pages"""
    if root is None:
        root = Path.cwd()

    yield from (cast(TalentPage, page)
                for page in pages_under(root / 'content/w', '*.md')
                if page.path.stem != '_index')

def all_event_pages(root: Optional[Path]=None, verbose: bool = False, sink=None) -> Iterable[EventPage]:
    """Walk the files and produce all event pages"""
    if root is None:
        root = Path.cwd()

    yield from (cast(EventPage, page)
                for page in pages_under(root / 'content/e', '**/????-??-??-*.md', verbose, sink))

def pages_under(path: Path, glob_pattern: str = '*.md', verbose: bool = False, sink=None) -> Iterable[Page]:
    error_sink = sink or default_sink()
    yield from (page(doc, verbose=verbose)
                for page_path in path.glob(glob_pattern)
                if (doc := RichDoc.from_file(page_path, error_sink)))

if __name__ == "__main__":
    path = Path(sys.argv[1])
    pg = page(path)
    breakpoint()
