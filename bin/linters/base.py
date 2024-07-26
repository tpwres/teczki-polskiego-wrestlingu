from abc import abstractmethod
from pathlib import Path
from contextlib import AbstractContextManager, contextmanager
from io import TextIOBase, StringIO
import sys

class LintError:
    def supports_auto(self):
        return False

    def message(self, file_root: Path) -> str:
        return "LintError(???)"

    def calculate_fix(self, body_text):
        raise NotImplementedError

class Changeset:
    def apply_changes(self, path: Path):
        raise NotImplementedError

class Doc:
    """
    A class that wraps either a path or stdin, abstracting operations
    like reading, writing or accessing the filename.
    """

    # Like Path.open. Must return a context mgr which yields an IO object.
    @abstractmethod
    def open(self, mode='r') -> AbstractContextManager[TextIOBase]: pass

    # Like PurePath.match
    @abstractmethod
    def match(self, name) -> bool: pass

    # Like Path.relative_to
    @abstractmethod
    def relative_to(self, other) -> str: pass

    @abstractmethod
    def pathname(self) -> Path: pass

class FileBackedDoc(Doc):
    def __init__(self, path: Path):
        self.path = path

    def open(self, mode='r'):
        return self.path.open(mode)

    def match(self, pattern):
        return self.path.match(pattern)

    def relative_to(self, other):
        return self.path.relative_to(other)

    def pathname(self):
        return self.path

@contextmanager
def io_context_manager(stringio):
    # Every time we open it, rewind to beginning
    stringio.seek(0)
    yield stringio

class StreamDoc(Doc):
    def __init__(self):
        self.io = StringIO(sys.stdin.read())

    def dump(self):
        sys.stdout.write(self.io.getvalue())

    def open(self, mode='r'):
        return io_context_manager(self.io)

    def match(self, pattern):
        return False

    def relative_to(self, pattern):
        return '<stdin>'

    def pathname(self):
        return Path('-')

