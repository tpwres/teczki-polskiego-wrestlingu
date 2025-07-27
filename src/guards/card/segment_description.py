from pathlib import Path

from guards.main.base import Base
from parse import blocks
from card import Card
import yaml

class SegmentDescription(Base):
    @classmethod
    def accept_path(cls, path: Path):
        is_event_article = path.is_relative_to('content/e')

        return is_event_article

    def validate_card(self, card: blocks.CardBlock):
        raw_card = card.raw_card
        if not raw_card:
            return


        for i, row in enumerate(raw_card, 1):
            match row:
                case [*opponents, {'g': segment_value} as options]:
                    if isinstance(segment_value, str):
                        continue
                    stip = options.get('s')
                    if segment_value == True and not stip:
                        self.log_error(f"Match {i}: missing segment text. Set it as the value of g: option, or (deprecated) set g: true, s: segment description")
