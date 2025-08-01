from pathlib import Path
from typing import Any

from guards.main.base import Base
from parse import blocks

class SegmentDescription(Base):
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

        for i, row in enumerate(raw_card, 1):
            match row:
                case [*_, {'g': segment_value} as options]:
                    if isinstance(segment_value, str):
                        continue
                    stip = options.get('s')
                    if segment_value == True and not stip:
                        self.log_error(f"Match {i}: missing segment text."
                            "Set it as the value of g: option, or (deprecated) set g: true, s: segment description"
                        )
