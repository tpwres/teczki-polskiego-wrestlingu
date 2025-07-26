from pathlib import Path

from ..main.base import Base
from parse import blocks
from card import Card
import yaml

class CardOptionsCorrect(Base):
    @classmethod
    def accept_path(cls, path: Path):
        is_event_article = path.is_relative_to('content/e')

        return is_event_article

    def validate_card(self, card: blocks.CardBlock):
        params = {
            key: value
            for key, value in (
                    pair.split('=')
                    for pair in card.params.split(",")
            )
        }
        predicted = params.get('predicted') == 'true'
        incomplete = params.get('incomplete') == 'true'
        unofficial = params.get('unofficial') == 'true'

        if predicted:
            self.check_all_matches_are_upcoming(card.raw_card)

    def check_all_matches_are_upcoming(self, card):
        for i, row in enumerate(card):
            match row:
                case [*opponents, {"nc": "upcoming"}]:
                    pass
                case [*opponents]:
                    breakpoint()
                    self.log_error(f"Match {i}: missing nc: upcoming")
                case dict(delim_or_credits):
                    pass
