from pathlib import Path

from guards.main.base import Base
from parse import blocks
from typing import Optional, Any

class CardSeen(Base):
    @classmethod
    def accept_path(cls, path: Path):
        return path.is_relative_to('content/e')

    @classmethod
    def accept_frontmatter(cls, frontmatter: dict[str, Any]) -> bool:
        template = frontmatter.get('template')
        return template == 'event_page.html'

    def __init__(self):
        super().__init__()
        self.card_seen_at: Optional[int] = None
        self.skip_card_seen_at: Optional[int] = None

    def validate_text(self, text: blocks.TextBlock):
        for line_num, line in enumerate(text.body):
            if "{{ skip_card() }}" in line:
                self.skip_card_seen_at = text.starting_line + line_num
                return

    def validate_card(self, card: blocks.CardBlock):
        self.card_seen_at = card.starting_line

    def finalize(self):
        match (self.skip_card_seen_at, self.card_seen_at):
            case (int(skip_seen), int(card_start)):
                self.log_error(f"Document has both {{ skip_card() }} in line {skip_seen} and card in line {card_start}")
            case (int(), None) | (None, int()):
                pass # This is Correct
            case (None, None):
                self.log_error("Missing card block. If the event has no known card, use {{ skip_card() }}.")
