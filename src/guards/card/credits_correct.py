from pathlib import Path
from typing import Any

from guards.main.base import Base
from parse import blocks

class CreditsCorrect(Base):
    @classmethod
    def accept_path(cls, path: Path):
        return path.is_relative_to('content/e')

    @classmethod
    def accept_frontmatter(cls, frontmatter: dict[str, Any]) -> bool:
        template = frontmatter.get('template')
        return template == 'event_page.html'

    def validate_card(self, card: blocks.CardBlock):
        raw_card = card.raw_card
        if not raw_card:
            return

        credits_seen = False

        for i, row in enumerate(raw_card, 1):
            if credits_seen:
                # TODO: Message points to start of card block, not actual line number
                self.log_error("Credits must be the last element in the card", line_number=card.starting_line)
                return

            match row:
                case {"credits": dict(credits)}:
                    credits_seen = True
                case _:
                    continue
