import re
from typing import Iterable, Optional
from pathlib import Path
from dataclasses import dataclass
from .base import LintError, Changeset, Doc
from card import Card, Match
from utils import parse_front_matter
from articles import load_existing_name_articles
from rewriter import Rewriter, UpdateMatch

@dataclass
class ReplaceCard(Changeset):
    text: str

    def apply_changes(self, path: Doc):
        with path.open('r') as fp:
            card_text = fp.read()
            card = Card(card_text)
            start_offset, end_offset = card.start_offset, card.end_offset
            fp.close()

            new_text = card_text[:start_offset] + self.text + card_text[end_offset:]
            with path.open('w') as fp:
                fp.write(new_text)
        return True

@dataclass
class UnlinkedParticipantError(LintError):
    path: Doc
    match_index: int
    name: str
    link: str

    def __str__(self):
        return "Match {}: replace {} with link {}".format(self.match_index + 1, self.name, self.link)

    def message(self, file_root: Path):
        return "[{}] {}".format(self.path.relative_to(file_root), self)

    def supports_auto(self):
        return True

    def calculate_fix(self, text) -> Optional[Changeset]:
        card = Card(self.path.open())
        if not card.matches: return None

        with self.path.open() as fp:
            card_lines = fp.read()[card.start_offset:card.end_offset]
            rewriter = Rewriter(card_lines)
            rx = self.prepare_regex(self.name)
            rewriter.add_replacement(UpdateMatch(self.match_index, rx, self.link))
            result = rewriter.rewrite()
            return ReplaceCard(result)

    def prepare_regex(self, text: str) -> re.Pattern:
       escaped = re.escape(text) 
       head_alpha, tail_alpha = text[0].isalnum(), text[-1].isalnum()
       boundary = r'\b'

       return re.compile(f"{boundary if head_alpha else ''}{escaped}{boundary if tail_alpha else ''}")


class UnlinkedParticipantLinter:
    def __init__(self):
        self.names_with_articles = load_existing_name_articles()

    def lint(self, path: Path):
        with path.open('r') as fp:
            card = Card(fp)
            if not card.matches:
                return []

            return self.analyze_matches(card.matches, path)

    def analyze_matches(self, matches: Iterable[Match], path: Path) -> list[LintError]:
        errors = []
        for m in matches:
            participants = list(m.all_names())
            unlinked_participants = [p for p in participants if p.link is None]
            # Unlinked participants are only flagged if a personal file already exists
            for up in unlinked_participants:
                article = self.names_with_articles.get(up.name)
                if not article: continue

                link = "[{}](@/w/{})".format(up.name, article.name)
                errors.append(UnlinkedParticipantError(path, m.index, up.name, link))

        return errors
