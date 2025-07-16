"""
Concept: a Rich Doc represents a Zola markdown document, possibly with special sections based on project-specific markup. It's somewhat like an AST, but only goes one level deep.
A zola document has the following properties and elements
1. front matter, which is a TOML block. Certain properties can be read from it, e.g. template. This is also where the photo gallery is defined.
2. text up to <!-- more -->, which is called the summary If this HTML comment is absent, there is no summary
3. body text

A Rich Doc improves this by further parsing the body text into a list of blocks. A block can be one of:
- markdown text, which can further be broken down into sections
- recognized Zola tag, in turn containing text or other markup
  - most importantly, card()
  - but also free_card(), timeline()
- other blocks like championship(), org_badge() appear mixed with markdown text
"""

from collections import namedtuple
from dataclasses import dataclass
from typing import Optional, TextIO, Any
from pathlib import Path, PurePath
from io import StringIO

from .blocks import BlockRegistry, FrontMatterBlock, Block, CardBlock, TextBlock

Section = namedtuple('Section', ['start', 'id', 'block'])

@dataclass
class RichDoc:
    path: Path|PurePath
    front_matter: dict[str, Any]
    summary: Optional[str]
    sections: list[Section]

    @property
    def title(self) -> Optional[str]:
        return self.front_matter.get('title')

    @property
    def template(self) -> Optional[str]:
        return self.front_matter.get('template')

    @property
    def taxonomies(self) -> dict[str, Any]:
        return self.front_matter.get('taxonomies') or {}

    @property
    def card_section(self) -> Optional[tuple[int, Optional[str], CardBlock]]:
        "Returns the first card block found, or None if no card blocks."
        card_sections = [section for section in self.sections if isinstance(section.block, CardBlock)]
        if card_sections:
            return card_sections[0]




...
