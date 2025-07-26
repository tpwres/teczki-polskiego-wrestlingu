from pathlib import Path
from parse import blocks

class Base:
    # A Guard is a class inheriting from Base.
    # It can have methods that accept different types of blocks (see parser.blocks).
    # To skip a block just don't define a method, the default from Base will do nothing.
    # During operation, a Guard emits Issues which signal a problem with a block.
    # An issue may also come with a Fix, which is a callable to be ran against the block text to fix the issue.

    def __init__(self):
        self.issues = []

    @classmethod
    def accept_frontmatter(cls, frontmatter: blocks.FrontMatterBlock):
        """Returns false if, based on the front matter block, this Guard should not process the file.
           Otherwise, returns True.
        """
        return True

    @classmethod
    def accept_path(cls, path: Path):
        """Returns False, if based on the filename, this Guard should not process the file.
           Otherwise, returns True.
           Is usually called before accept_frontmatter.
        """
        return True

    def validate_frontmatter(self, frontmatter: blocks.FrontMatterBlock):
        """Validate the front matter block."""
        pass

    def validate_card(self, card: blocks.CardBlock):
        pass

    def validate_text(self, text: blocks.TextBlock):
        pass

    def validate_block(self, block: blocks.Block):
        """Invoked for blocks of other types (free_card, timeline and any others)."""
        pass
