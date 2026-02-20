import re
from datetime import datetime, date
from pathlib import Path
from card import Card
import tomllib
from sys import exit, stderr
from typing import Tuple, Iterable, Optional
from io import TextIOBase


FrontMatterPrimitive = str | int | float
FrontMatterValue = FrontMatterPrimitive | list[FrontMatterPrimitive] | dict[str, FrontMatterPrimitive]
FrontMatter = dict[str, FrontMatterValue]

class Page:
    path: Path
    front_matter: FrontMatter
    front_offset: int
    body: str

    def __init__(self, io: TextIOBase, verbose: bool = True):
        if verbose:
            print("Loading %s" % path)

        self.path = Path(io.name)
        self.front_matter, self.front_offset, self.body = self.parse_content(io)

    def parse_content(self, io: TextIOBase) -> Tuple[FrontMatter, int, str]:
        line = io.readline()
        if line.strip() != '+++':
            breakpoint()
            raise ValueError(f"Page `{self.path}` did not start with frontmatter delimiter `+++`")

        matter = []
        while True:
            line = io.readline()
            if not line: # readline returns empty str, not even a single "\n" at eof
                raise ValueError(f"Front matter block closing delimiter not found in `{self.path}`")
            elif line.strip() == '+++':
                break
            matter.append(line)

        fm = tomllib.loads("\n".join(matter))
        return (fm, len(matter), io.read())

    @property
    def title(self): return self.front_matter['title']

    def __repr__(self):
        return f"<{self.__class__.__name__}({self.path})>"

class EventPage(Page):
    event_date: date
    orgs: list[str]
    card: Card

    date_org_re = re.compile(r'^(?P<date>\d{4}-\d\d-\d\d)-(?P<orgs>[^-]+)')

    def __init__(self, io: TextIOBase, verbose: bool = True):
        super().__init__(io, verbose)

        match EventPage.date_org_re.match(self.path.stem):
            case re.Match() as m:
                ymd = m.group('date')
                self.event_date = datetime.strptime(ymd, '%Y-%m-%d').date()
                self.orgs = m.group('orgs').split('_')

        self.card = Card(self.body, self.path, self.front_offset)

    def __repr__(self):
        return f"<EventPage({self.path}) date={self.event_date} orgs={self.orgs}>"


class OrgPage(Page):
    pass

class VenuePage(Page):
    pass

class TalentPage(Page):
    def __repr__(self):
        title = self.front_matter.get('title', None)
        return f"<TalentPage({self.path}) name={title!r}>"

class Article(Page):
    pass

def page(path: Path, verbose: bool = False) -> Page:
    """Returns a subclass of Page, based on what's the most appropriate
    for the path given."""
    # DEPRECATED, should be replaced with .page on a FileSystemtree or ZipContentTree
    if Path('content/e') in path.parents or EventPage.date_org_re.match(path.stem):
        return EventPage(path, verbose)
    elif path.match('o/*.md'):
        return OrgPage(path, verbose)
    elif path.match('w/*.md'):
        return TalentPage(path, verbose)
    elif path.match('v/*.md'):
        return VenuePage(path, verbose)
    else:
        return Article(path, verbose)

def all_talent_pages(root: Optional[Path]=None) -> Iterable[TalentPage]:
    """Walk the files and produce all talent pages"""
    if root is None:
        root = Path.cwd()

    yield from (TalentPage(page_path)
                for page_path in (root / 'content/w/').glob('*.md')
                if page_path.stem != '_index')

def all_event_pages(root: Optional[Path]=None, verbose: bool = False) -> Iterable[EventPage]:
    """Walk the files and produce all event pages"""
    if root is None:
        root = Path.cwd()

    yield from (EventPage(page_path, verbose=verbose)
                for page_path in (root / 'content/e/').glob('**/????-??-??-*.md')
                if page_path.stem != '_index')

def pages_under(path: Path, verbose: bool = False) -> Iterable[Page]:
    yield from (page(page_path, verbose=verbose)
                for page_path in path.glob('*.md'))

if __name__ == "__main__":
    import sys, code
    path = Path(sys.argv[1])
    pg = page(path)
    code.interact(local=locals())
