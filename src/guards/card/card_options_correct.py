from pathlib import Path
from typing import Any

from guards.main.base import Base
from parse import blocks

class CardOptionsCorrect(Base):
    @classmethod
    def accept_path(cls, path: Path):
        return path.is_relative_to('content/e')

    @classmethod
    def accept_frontmatter(cls, frontmatter: dict[str, Any]) -> bool:
        template = frontmatter.get('template')
        return template == 'event_page.html'

    def __init__(self):
        self.reason = None
        self.required_title = None
        self.card_header_title = None

    def validate_text(self, text: blocks.TextBlock):
        if text.title is None:
            return
        if 'card' not in text.title.lower():
            return
        self.card_header_title = text.title

    def finalize(self):
        if not (self.card_header_title and self.required_title):
            return

        if self.required_title.lower() != self.card_header_title.lower():
            message = f'Section with card should be titled "{self.required_title}"'
            if self.reason:
                message += self.reason
            self.log_error(message)

    def validate_card(self, card: blocks.CardBlock):
        if not card.params:
            return

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
            self.required_title = 'Predicted card'
            self.reason = ' because card(predicted=true) was used'
            self.check_all_matches_are_upcoming(card.raw_card)

    def check_all_matches_are_upcoming(self, card):
        for i, row in enumerate(card):
            match row:
                case [*opponents, {"nc": "upcoming"}]:
                    pass
                case [*opponents]:
                    self.log_error(f"Match {i}: missing nc: upcoming. All matches in a predicted card must have that flag.")
                case dict(delim_or_credits):
                    pass
