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

from typing import Optional, Tuple
from pathlib import Path, PurePath
from typing import TextIO, Any, ClassVar
from io import StringIO
from functools import partial
import re
import tomllib
import yaml
from linters.errors import format_error
from blocks import BlockRegistry, FrontMatterBlock, Block, CardBlock

class DocError(Exception):
    pass

class ParseError(Exception):
    pass

FRONTMATTER_DELIMITER = re.compile(r'[+]{3}\s*')
MORE_REGEX = re.compile(r'<!--\s+more\s+-->\s*')
BLOCK_START = re.compile(r'''
  \s*
  \{%\s+ # Wrapped in {% %}
    (?P<name>[\w_]+)
    \( # Keyword followed by mandatory parentheses
      (?P<params>
         (?: # Params are one or more keyword=value, joined with commas
           \w+ = # keyword, equals sign with no spaces
           (?:
             \w+ | # Either a named const (True or False) or numeric value
             (?P<delim>["']).+?(?P=delim) # Or a string value
           )
           ,?\s*
         )*
      )
    \)\s+
  \%}\s*
''', re.X)
BLOCK_END = re.compile(r'\s*{%\s+end\s+%}\s*')
HEADER_LINE = re.compile(r'^[#]{2,5}\s+(?P<title>.*)$')
ALL_BLANKS = re.compile(r'^\s+$')

class RichDoc:
    body: str
    path: Path
    frontmatter: dict()
    summary: Optional[str]
    sections: list[Any]


    @classmethod
    @classmethod
    def from_file(cls, path: Path, error_sink=None):
        if not path.exists():
            error_sink.error(DocError(f"Path {path} does not exist"))
            return cls(StringIO(''), path, error_sink)

        doc = cls(path.open('r'), path, error_sink)
        doc.parse()
        return doc

    @classmethod
    def from_text(cls, body: TextIO, identifier: str = '<text>', error_sink = None):
        doc = cls(StringIO(body), PurePath(identifier), error_sink)
        doc.parse()
        return doc

    @property
    def title(self) -> Optional[str]:
        return self.front_matter.get('title')

    @property
    def template(self) -> Optional[str]:
        return self.front_matter.get('template')

    @property
    def taxonomies(self) -> dict[str, Any]:
        return self.front_matter.get('taxonomies') or {}

    def __init__(self, body: TextIO, path: Optional[Path], error_sink=None):
        self.body = body
        self.path = path
        self.sink = error_sink
        self.sections = []

        self.current_block = None
        self.last_section_title = None
        self.front_matter = {}
        self.body_lines = []

    def parse(self):
        # Event-consumer style
        for line_num, line in enumerate(self.body, start=1):
            if FRONTMATTER_DELIMITER.match(line):
                self.frontmatter_delimiter(line_num)
            elif MORE_REGEX.match(line):
                self.summary_closed(line_num)
            elif BLOCK_END.match(line):
                self.block_closed(line_num)
            elif mm := HEADER_LINE.match(line):
                self.section_header(mm.group('title'), line, line_num)
            elif mm := BLOCK_START.match(line):
                self.block_opened(mm.group('name'), mm.group('params'), line_num)
            else:
                self.raw_text(line, line_num)

        final_text, final_block_start = self.text_up_to_now() or (None, None)
        if final_text:
            self.sections.append((final_block_start, self.last_section_title, final_text))

        self.prune_empty_sections()

    def prune_empty_sections(self):
        self.sections = [(ln, title, body)
                         for ln, title, body in self.sections
                         if isinstance(body, Block) # Pass through block sections
                         or not ALL_BLANKS.match(body)]

    def frontmatter_delimiter(self, line_num):
        if self.current_block:
            # Assume current block is a FrontMatterBlock
            self.block_closed(line_num)
            # Now remove it from sections, it's special
            _, _, fm = self.sections.pop()
            self.front_matter = fm.front_matter
        else:
            if self.front_matter:
                self.sink.error(format_error(f"extra frontmatter delimiter encountered", self.path, line_num, None))

            # No need to wrap up preceding text, this is at document start
            self.current_block = FrontMatterBlock(None, line_num, self.sink)

    def summary_closed(self, line_num):
        summary, _ = self.text_up_to_now()
        # NOTE: not calling clear_buf() - we want the text to remain
        self.summary = summary.strip()

    def section_header(self, title, line, line_num):
        # If we're in a block, don't create sections
        if self.current_block:
            self.raw_text(line, line_num)
            return

        # Wrap up current text and add as section
        section_text, start_line = self.text_up_to_now()
        self.clear_buf()

        self.sections.append((start_line, self.last_section_title, section_text))

        # Include header as part of section body
        self.raw_text(line, line_num)

        self.last_section_title = title

    def block_opened(self, block, params, line_num):
        # Wrap up current text and add as section
        section_text, start_line = self.text_up_to_now() or (None, None)
        self.clear_buf()

        if section_text:
            self.sections.append((start_line, self.last_section_title, section_text))

        if self.current_block:
            self.sink.error(format_error("opening new block before closing previous one", self.path, line_num, None))
        self.current_block = self.create_block(block, params, line_num)

    def block_closed(self, line_num):
        self.sections.append((
            self.current_block.starting_line,
            f'<{self.current_block.__class__.__name__}>',
            self.current_block
        ))

        try:
            self.current_block.close()
        except ParseError as p:
            self.sink.parse_error(p, self.path, self.current_block.starting_line)
        finally:
            self.current_block = None
            self.last_section_title = None

    def create_block(self, block, params, line_num) -> Block:
        return BlockRegistry.create_block(block, params, line_num, self.sink)

    def raw_text(self, line, line_num):
        # Feed text to block if one is open, otherwise to body buffer
        if self.current_block:
            self.current_block.text(line, line_num)
            return

        self.body_lines.append((line_num, line))

    def text_up_to_now(self) -> Optional[Tuple[str, int]]:
        if not self.body_lines:
            return None

        text = '\n'.join([line for _, line in self.body_lines])
        start_line, _ = self.body_lines[0]
        return (text, start_line)

    def clear_buf(self):
        self.body_lines = []



if __name__ == "__main__":
    doc = RichDoc.from_file(Path("content/a/grand-timeline.md"))
    # RichDoc.from_file(Path("content/e/low/2025-04-06-low-2.md"))
    # RichDoc.from_file(Path("content/c/ppw-championship.md"))
    breakpoint()

...
