from pathlib import Path
from collections import namedtuple
from itertools import pairwise
from typing import Any

from parse import blocks
from guards.main.base import Base

Header = namedtuple('Header', ['title', 'level', 'line'])

class EventHeaders(Base):
    """
    Verifies if section headers have the recommended structure.
    See doc/TOC.md
    """

    @classmethod
    def accept_path(cls, path: Path):
        return path.is_relative_to('content/e')

    @classmethod
    def accept_frontmatter(cls, frontmatter: dict[str, Any]) -> bool:
        template = frontmatter.get('template')
        return template == 'event_page.html'

    def __init__(self):
        super().__init__()
        self.headers: list[Header] = []
        self.predicted_card = False

    def validate_text(self, text: blocks.TextBlock):
        # In text blocks, .params contains the extracted title
        title = text.params
        if not title:
            return

        level = self.extract_level(text.body)
        self.headers.append(Header(title, level, text.starting_line))

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
        self.predicted_card = params.get('predicted') == 'true'

    recommended_levels = {
        'Storyline overview': 2,
        'Build-up': 2,
        'Card': 2,
        'Predicted card': 2,
        'Recap': 3,
        'Higlights': 3,
        'References': 2,
    }

    def finalize(self):
        self.check_header_levels()
        self.check_header_order()

    def check_header_levels(self):
        for header in self.headers:
            recommended = self.recommended_levels.get(header.title, None)
            if recommended is not None and recommended != header.level:
                self.log_error(f'Section "{header.title}" level should be {recommended}', line_number=header.line)

    def check_header_order(self):
        ordering = list(self.recommended_levels.keys())
        actual_order = [(ordering.index(header.title), header.title, header.line)
                        for header in self.headers
                        if header.title in ordering]
        for (l_index, l_title, l_line), (r_index, r_title, r_line) in pairwise(actual_order):
            if r_index < l_index:
                # Not ideal, just a start
                self.log_error(f'Section "{l_title}" out of order, should be after section "{r_title}" at line {r_line}', line_number=l_line)


    def extract_level(self, body_text: list[str]):
        text = ''.join(body_text) # Already has newlines
        if text.startswith('#####'):
            return 5
        elif text.startswith('####'):
            return 4
        elif text.startswith('###'):
            return 3
        elif text.startswith('##'):
            return 2
        elif text.startswith('#'):
            return 1
        return 0 # Initial paragraph
