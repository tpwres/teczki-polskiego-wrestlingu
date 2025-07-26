from pathlib import Path

from ..main.base import Base
from parse import blocks
from card import Card
import yaml

class DelimitersCorrect(Base):
    @classmethod
    def accept_path(cls, path: Path):
        is_event_article = path.is_relative_to('content/e')

        return is_event_article

    def validate_card(self, card: blocks.CardBlock):
        raw_card = card.raw_card
        last_date_seen = None

        for i, row in enumerate(raw_card, 1):
            match row:
                case {"d": str(delim_text), "date": date}:
                    if last_date_seen and date <= last_date_seen:
                        self.log_error(f"Delimiter row {i}: date {date} is before previous delimiter date {last_date_seen}")
                case {"d": str(text)}:
                    pass
                case _:
                    continue
