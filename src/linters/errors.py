from .base import LintError
from dataclasses import dataclass
from typing import Optional
from pathlib import Path


@dataclass
class FileError(LintError):
    path: Optional[Path]
    text: str

    def message(self, file_root: Optional[Path]):
        match self.path:
            case Path():
                if file_root:
                    return f'[{self.path.relative_to(file_root)}] Error: {self.text}'
                else:
                    return f'[{self.path}] Error: {self.text}'
            case _:
                return f'[????] Error: {self.text}'

    @property
    def supports_auto(self):
        return False

    @property
    def fatal(self):
        return True

class LintWarning(LintError): pass

@dataclass
class FileWarning(LintWarning):
    path: Optional[Path]
    text: str

    def message(self, file_root: Optional[Path]):
        match self.path:
            case Path():
                if file_root:
                    return f'[{self.path.relative_to(file_root)}] Warning: {self.text}'
                else:
                    return f'[{self.path}] Warning: {self.text}'
            case _:
                return f'[????] Warning: {self.text}'

    @property
    def supports_auto(self):
        return False

    @property
    def fatal(self):
        return False
