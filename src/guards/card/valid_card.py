from pathlib import Path
from typing import Any

from guards.main.base import Base
from parse import blocks

class ValidCard(Base):
    @classmethod
    def accept_path(cls, path: Path):
        return path.is_relative_to('content/e')

    @classmethod
    def accept_frontmatter(cls, frontmatter: dict[str, Any]) -> bool:
        template = frontmatter.get('template')
        return template == 'event_page.html'


    def validate_card(self, card: blocks.CardBlock):
        raw_card = card.raw_card
        # At this point we know that YAML parsed correctly. Any issues with that
        # were reported before the linter was run.

        # To check:
        # - card is not empty
        # - card is a list, each item of that either a list or a dict
        # - if a list, must not be empty, and of the correct shape: [opponent, opponent, {options}]
        # - each opponent is a string, and options only contains supported ones

        match raw_card:
            case [] | None:
                self.log_error('Card is empty. Use a {{ skip_card() }} shortcode instead.', line_number=card.starting_line)
                return
            case [*rows, dict(unused_credits_row)]:
                self.check_matches(rows)
            case [*rows]:
                self.check_matches(rows)

    def check_matches(self, rows):
        for i, row in enumerate(rows, 1):
            row_options = None

            match row:
                case dict(delim_or_credits):
                    pass
                case [str(single_opponent)]:
                    self.log_error(f"Match {i}: cannot have a single person listed without any options. Add at least a s:, or if it was a segment, add it with g:")
                case [str(single_opponent), dict(options)]:
                    if 's' in options or 'g' in options:
                        row_options = options
                    else:
                        self.log_error(f"Match {i}: cannot have a single person listed without s: or g: options.")
                case [*opponents] if all(isinstance(el, str) for el in opponents):
                    pass
                case [*opponents, dict(options)] if all(isinstance(el, str) for el in opponents):
                    row_options = options
                case [*opponents, dict(options)]:
                    self.log_error(f"Match {i}: all elements except the trailing options must be strings.")
                case _:
                    self.log_error(f"Match {i}: malformed row {row}")

            if row_options:
                self.check_valid_options(f"Match {i}", row_options)

    # TODO: think about extracting to a separate guard
    def check_valid_options(self, location, row_options: dict):
        accepted_options = {
            'nc': str,
            's': str,
            'g': (bool, str),
            'r': str,
            'c': str,
            'n': (list, str)
        }
        for option, types in accepted_options.items():
            if not option in row_options:
                continue

            value = row_options[option]
            if not isinstance(value, types):
                self.log_error(f"{location}: option {option} is of invalid type")

        if 'r' in row_options and 'nc' in row_options:
            self.log_error(f"{location}: Cannot have both r: and nc: in a single match")
