from pathlib import Path
from parse import blocks
from parse.logger import RichDocLogger
from typing import Any
import re

class Base:
    # A Guard is a class inheriting from Base.
    # It can have methods that accept different types of blocks (see parser.blocks).
    # To skip a block just don't define a method, the default from Base will do nothing.
    # During operation, a Guard emits Issues which signal a problem with a block.
    # An issue may also come with a Fix, which is a callable to be ran against the block text to fix the issue.

    logger: RichDocLogger
    path: Path

    def __init__(self):
        pass

    @classmethod
    def accept_frontmatter(cls, frontmatter: dict[str, Any]) -> bool:
        """Returns false if, based on the front matter block, this Guard should not process the file.
           Otherwise, returns True.
        """
        return True

    @classmethod
    def accept_path(cls, path: Path) -> bool:
        """Returns False, if based on the filename, this Guard should not process the file.
           Otherwise, returns True.
           Is usually called before accept_frontmatter.
        """
        return True

    def validate_frontmatter(self, frontmatter: dict[str, Any], block: blocks.FrontMatterBlock):
        """Validate the front matter block."""
        pass

    def validate_card(self, card: blocks.CardBlock):
        """Validate"""
        pass

    def validate_card_ast(self, ast: list['yaml.tokens.Token'], card: blocks.CardBlock):
        pass

    def validate_text(self, text: blocks.TextBlock):
        pass

    def validate_block(self, block: blocks.Block):
        """Invoked for blocks of other types (free_card, timeline and any others)."""
        pass

    def finalize(self):
        """Invoked after passing all blocks, for validators that need to keep state
        and report only after the whole file was consumed.
        """
        pass

    # Logging through RichDocLogger
    def log_error(self, message, **kwargs):
        self.logger.log_error(message, **kwargs)

    def log_warning(self, message, **kwargs):
        self.logger.log_warning(message, **kwargs)


    def skip_lint_instruction(self, line: str) -> bool:
        """If line contains a trailing comment of the form:
           # skip: GuardName (followed by any content)
           return True, otherwise False.
        """
        # Extract the current guard name
        current_guard_name = self.__class__.__name__

        # Check if the line contains a skip instruction for this guard
        skip_pattern = rf"#\s*skip:\s*{current_guard_name}\b"
        return bool(re.search(skip_pattern, line))
