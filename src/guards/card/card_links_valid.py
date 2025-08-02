from pathlib import Path
from yaml import tokens as t
from typing import Any
from mistletoe import Document
from mistletoe.markdown_renderer import MarkdownRenderer

from guards.main.base import Base
from guards.main.state_machine import CardStateMachine
from guards.main.markup import find_links
from parse import blocks

class CardLinksValid(Base):
    """Inspects all text tokens in a card: opponent names, text in segments etc, and ensures all links within are valid.
    Similar to ContentLinks but reads the card, not text blocks."""

    @classmethod
    def accept_path(cls, path: Path):
        return path.is_relative_to('content/e')

    @classmethod
    def accept_frontmatter(cls, frontmatter: dict[str, Any]) -> bool:
        template = frontmatter.get('template')
        return template == 'event_page.html'


    def validate_card_ast(self, ast: list[t.Token], card: blocks.CardBlock):
        self.card_starting_line = card.starting_line
        with MarkdownRenderer() as renderer:
            callback = lambda token, *args: self.check_links(renderer, token, *args)
            sm = CardStateMachine(ast,
                crew_entry=callback,
                match_opponent=callback,
                option_value=callback,
                special_option_value=callback
            )
            # Consume state machine but do nothing with the results
            for token, replacement in sm:
                pass


    def check_links(self, renderer, token, *args):
        doc = Document(token.value)
        token_line = token.start_mark.line
        for link, linenum in find_links(doc):
            if link.dest_type != 'uri':
                # The other types are angle_uri and full, both of which take a complete url, but angle_uri has no label.
                continue

            formatted_link = "".join(renderer.render(link)).rstrip()
            if link.target.startswith('content/'):
                self.report_content_link(formatted_link, linenum + token_line, self.card_starting_line)
            elif link.target.startswith('@') and self.destination_file_missing(link.target):
                self.report_missing_target(formatted_link, linenum + token_line, self.card_starting_line)

    def destination_file_missing(self, link_target: str) -> bool:
        target, _, _ = link_target.partition('#')
        path = Path('content') / target[2:] # Strip @/
        return not path.exists()

    def report_content_link(self, formatted_link: str, relative_linenum: int, starting_line: int):
        self.log_error(f"`{formatted_link}` links to content/. Replace the target to start with `@` instead.", line_number=starting_line + relative_linenum)

    def report_missing_target(self, formatted_link: str, relative_linenum: int, starting_line: int):
        self.log_error(f"`{formatted_link}` links to a non-existent file. The filename may be misspelled, or not created yet.", line_number=starting_line + relative_linenum)
