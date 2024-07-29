from pathlib import Path
from dataclasses import dataclass
from .base import LintError
from card import Card

@dataclass
class MissingCard(LintError):
    path: Path

    def message(self, file_root: Path):
        return "[{}] Missing card block {{% card() %}} .. {{% end %}}".format(self.path.relative_to(file_root))

    def supports_auto(self):
        return False

class MissingCardLinter:
    def __init__(self, config):
        pass

    def lint(self, path: Path):
        with path.open('r') as fp:
            text = fp.read()
            if '{{ skip_card() }}' in text:
                return []

        with path.open('r') as fp:
            card = Card(fp, path)
            if card.matches:
                return []

            return [MissingCard(path)]
