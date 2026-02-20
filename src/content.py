from zipfile import ZipFile
from fnmatch import fnmatch
from io import TextIOWrapper
from pathlib import Path
from page import EventPage, TalentPage, OrgPage, VenuePage, Article

class ContentCommon:
    def page(self, stream, verbose: bool = False):
        # Guess type of file from name, return appropriate Page object
        path = Path(stream.name)
        if Path('content/e') in path.parents or EventPage.date_org_re.match(path.stem):
            return EventPage(stream, verbose)
        elif path.match('o/*.md'):
            return OrgPage(stream, verbose)
        elif path.match('w/*.md'):
            return TalentPage(stream, verbose)
        elif path.match('v/*.md'):
            return VenuePage(stream, verbose)
        else:
            return Article(stream, verbose)

    def to_path(self, ioobj) -> Path:
        return Path(ioobj.name)

class FilesystemTree(ContentCommon):
    def __init__(self, root: Path):
        self.root = root

    def glob(self, glob: str, mode: str = 'rt'):
        for path in self.root.glob(glob):
            yield path.open(mode)

    def open(self, path, mode: str = 'rt'):
        return (self.root / 'content' / path).open(mode)

class ZipContentTree(ContentCommon):
    def __init__(self, zipfile_path: Path):
        self.archive = ZipFile(zipfile_path.open('rb'))

    def glob(self, glob: str, mode: str = 'rt'):
        # Zipfile does not handle mode=rt natively, always returns byte streams
        if 't' in mode:
            adjusted_mode = mode.replace('t', '')
            wrapper = lambda fp: TextIOWrapper(fp, encoding='utf-8')
        else:
            adjusted_mode, wrapper = mode, lambda fp: fp

        return (
            wrapper(self.archive.open(filename, adjusted_mode))
            for filename in self.archive.namelist()
            if fnmatch(filename, glob)
        )

    def open(self, path, mode: str = 'rt'):
        if 't' in mode:
            adjusted_mode = mode.replace('t', '')
            wrapper = lambda fp: TextIOWrapper(fp, encoding='utf-8')
        else:
            adjusted_mode, wrapper = mode, lambda fp: fp

        return wrapper(self.archive.open(path, adjusted_mode))

    @property
    def root(self) -> str:
        return 'content/' # Some code does subpath tests
