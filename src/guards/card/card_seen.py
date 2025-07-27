from pathlib import Path

from guards.main.base import Base
from parse import blocks
from card import Card

class CardSeen(Base):
    def __init__(self):
        super().__init__()
        self.card_seen = False

    def validate_card(self, card: blocks.CardBlock):
        self.card_seen = True

    def finalize(self):
        if not self.card_seen:
            self.log_error("Missing card block. If the event has no known card, use {{ skip_card() }}.")
