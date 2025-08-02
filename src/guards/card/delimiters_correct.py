from pathlib import Path
from typing import Any

from guards.main.base import Base
from parse import blocks

class DelimitersCorrect(Base):
    @classmethod
    def accept_path(cls, path: Path):
        return path.is_relative_to('content/e')

    @classmethod
    def accept_frontmatter(cls, frontmatter: dict[str, Any]) -> bool:
        template = frontmatter.get('template')
        return template == 'event_page.html'


    def validate_card(self, card: blocks.CardBlock):
        # TODO: Rewrite with statemachine card
        raw_card = card.raw_card
        if not raw_card:
            return

        last_date_seen = None

        for i, row in enumerate(raw_card, 1):
            match row:
                case {"d": str(delim_text), "date": date}:
                    if last_date_seen and date <= last_date_seen:
                        self.log_error(f"Delimiter row {i}: date {date} is before previous delimiter date {last_date_seen}")
                case {"d": str(text)}:
                    pass
                case {"d": _}:
                    self.log_error(f"Delimiter row {i}: title must be a string")
                case _:
                    continue
