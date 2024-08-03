import re
from datetime import datetime, date
from pathlib import Path
from card import Card
import tomllib
from sys import exit, stderr
from typing import Tuple
from io import TextIOBase


FrontMatterPrimitive = str | int | float
FrontMatterValue = FrontMatterPrimitive | list[FrontMatterPrimitive] | dict[str, FrontMatterPrimitive]
FrontMatter = dict[str, FrontMatterValue]

class Page:
    path: Path
    front_matter: FrontMatter
    body: str

    def __init__(self, path: Path, verbose: bool = True):
        if verbose:
            print("Loading %s" % path)

        self.path = path
        self.front_matter, self.body = self.parse_content(path.open('rt', encoding='utf-8'))

    def parse_content(self, io: TextIOBase) -> Tuple[FrontMatter, str]:
        line = io.readline()
        if line.strip() != '+++':
            raise ValueError(f"Page `{self.path}` did not start with frontmatter delimiter `+++`")

        matter = []
        line = io.readline()
        while True:
            matter.append(line)
            line = io.readline()
            if not line: # readline returns empty str, not even a single "\n" at eof
                raise ValueError(f"Front matter block closing delimiter not found in `{self.path}`")
            elif line.strip() == '+++':
                break

        fm = tomllib.loads("\n".join(matter))
        return (fm, io.read())

    @property
    def title(self): return self.front_matter['title']

class EventPage(Page):
    event_date: date
    orgs: list[str]
    card: Card

    date_org_re = re.compile(r'^(?P<date>\d{4}-\d\d-\d\d)-(?P<orgs>[^-]+)')

    def __init__(self, path: Path, verbose: bool = True):
        super().__init__(path, verbose)

        match EventPage.date_org_re.match(path.stem):
            case re.Match() as m:
                ymd = m.group('date')
                self.event_date = datetime.strptime(ymd, '%Y-%m-%d').date()
                self.orgs = m.group('orgs').split('_')

        self.card = Card(self.body, path)


class OrgPage(Page):
    pass

class TalentPage(Page):
    pass

class Article(Page):
    pass

def page(path: Path, verbose: bool = False) -> Page:
    """Returns a subclass of Page, based on what's the most appropriate
    for the path given."""
    if Path('content/e') in path.parents or EventPage.date_org_re.match(path.stem):
        return EventPage(path, verbose)
    elif Path('content/o') in path.parents:
        return OrgPage(path, verbose)
    elif Path('content/w') in path.parents:
        return TalentPage(path, verbose)
    else:
        return Article(path, verbose)

if __name__ == "__main__":
    import sys, code
    path = Path(sys.argv[1])
    pg = page(path)
    code.interact(local=locals())
