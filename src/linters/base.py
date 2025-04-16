from abc import abstractmethod
from pathlib import Path
from dataclasses import dataclass
from contextlib import AbstractContextManager, contextmanager, closing
from card import CardParseError, MatchParseError
from io import TextIOBase, StringIO
from yaml import MarkedYAMLError, YAMLError
from typing import TextIO, IO, Sequence, Optional, Protocol
import sys

class LintError:
    @property
    def fatal(self) -> bool:
        raise NotImplementedError

    @property
    def supports_auto(self) -> bool:
        raise NotImplementedError

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
    def open(self, mode='r') -> AbstractContextManager[IO]: pass

    # Like PurePath.match
    @abstractmethod
    def match(self, pattern) -> bool: pass

    # Like Path.relative_to
    @abstractmethod
    def relative_to(self, other) -> Path: pass

    @abstractmethod
    def pathname(self) -> Path: pass

class FileBackedDoc(Doc):
    def __init__(self, path: Path):
        self.path = path

    def open(self, mode='r'):
        return closing(self.path.open(mode))

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

    def relative_to(self, other):
        return Path('<stdin>')

    def pathname(self):
        return Path('-')

class Linter:
    def reset(self):
        """Reset state before parsing a new file"""
        pass

    @abstractmethod
    def lint(self, document: Doc) -> Sequence[LintError]:
        pass

    @abstractmethod
    def handles(self, path: Path) -> bool:
        "Return True if this path is one that this linter can handle."
        pass

class LinterProto(Protocol):
    @abstractmethod
    def handles(self, path: Path) -> bool:
        """Return True if this path is one that this linter can handle.
           The file may be opened and inspected if needed."""
        raise NotImplementedError

    @abstractmethod
    def lint(self, path: Path) -> Sequence[LintError]:
        raise NotImplementedError


    @abstractmethod
    def lint_stream(self, stream: TextIO) -> Sequence[LintError]:
        raise NotImplementedError

def line_offset_to_card_block(doc: Doc) -> Optional[int]:
    with doc.open() as fp:
        body = fp.read()
        index = body.index('{% card(')

    if index == -1: return None
    return body[:index].count('\n') + 1

@dataclass
class FileSyntaxError(LintError):
    doc: Doc
    error: YAMLError|CardParseError

    @property
    def fatal(self) -> bool:
        return True

    @property
    def supports_auto(self) -> bool:
        return False

    def message(self, file_root: Path) -> str:
        if file_root:
            path_section = f"[{self.doc.relative_to(file_root)}]"
        else:
            path_section = f"[{self.doc.pathname()}]"

        match self.error:
            case MarkedYAMLError(problem=problem, problem_mark=mark):
                # The file has a syntax error, we can't reliably parse the card.
                offset = line_offset_to_card_block(self.doc)
                # If the file doesn't have a card, we shouldn't be here anyway
                if offset is None:
                    raise ValueError("No card block detected when handling FileSyntaxError")

                if mark:
                    return f"{path_section} Syntax error: {problem} near line {offset + mark.line} column {mark.column}"
                else:
                    return f"{path_section} Syntax error: {problem}"
            case MatchParseError(args=[message, *_]):
                # Inherits from CardParseError, must be first
                return f"{path_section} Syntax error: {message}"
            case CardParseError(args=[message, *_]):
                return message
            case err:
                import pdb; pdb.set_trace()
                return f"{path_section} {err}"
