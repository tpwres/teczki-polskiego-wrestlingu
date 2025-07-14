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
from typing import Optional, Tuple, TextIO, Any
from pathlib import Path, PurePath
from io import StringIO
import re
import sys
from blocks import BlockRegistry, FrontMatterBlock, Block, CardBlock, TextBlock
from rich_doc_logger import RichDocLogger

Section = namedtuple('Section', ['start', 'id', 'block'])


@dataclass
class RichDoc:
    path: Path|PurePath
    front_matter: dict[str, Any]
    summary: Optional[str]
    sections: list[Any]

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
    def card_section(self) -> Optional[Tuple[int, Optional[str], CardBlock]]:
        "Returns the first card block found, or None if no card blocks."
        card_sections = [section for section in self.sections if isinstance(section.block, CardBlock)]
        if card_sections:
            return card_sections[0]


class RichDocParser:
    def __init__(self):
        self.logger = RichDocLogger()
        self.sections: list[Section] = []

        self.current_block: Optional[Block] = None
        self.last_section_title: Optional[str] = None
        self.front_matter: dict[str, Any] = {}
        self.body_lines: list[str] = []
        self.summary: Optional[str] = None

    def parse_file(self, path: Path) -> Optional[RichDoc]:
        with self.logger.parsing_context("RichDocParser.parse_file", path.as_posix()):
            if not path.exists():
                self.logger.log_error(f"File {path} not found")
                return None

            try:
                with path.open('r') as fp:
                    result = self.parse_stream(fp, path.as_posix())

                    if self.logger.has_errors():
                        self.logger.log_warning("Parsed with errors")
                        self.logger.print_report(sys.stderr)

                    return result
            except Exception as e:
                self.logger.log_exception(f"Failed to parse {path}", e)
                raise

    def parse_text(self, content: str, identifier: str = '<text>'):
        with self.logger.parsing_context("RichDocParser.parse_text", identifier):
            try:
                fp = StringIO(content)

                result = self.parse_stream(fp, identifier)

                if self.logger.has_errors():
                    self.logger.log_warning("Parsed with errors")

                return result
            except Exception as e:
                self.logger.log_exception("Failed to parse text", e)
                raise

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

    def parse_stream(self, stream: TextIO, path_or_ident: str):
        with self.logger.parsing_context("RichDocParser.parse_stream"):
            for line_num, line in enumerate(stream, start=1):
                if self.FRONTMATTER_DELIMITER.match(line):
                    self.frontmatter_delimiter(line_num)
                elif self.MORE_REGEX.match(line):
                    self.summary_closed(line_num)
                elif self.BLOCK_END.match(line):
                    self.block_closed(line_num)
                elif mm := self.HEADER_LINE.match(line):
                    self.section_header(mm.group('title'), line, line_num)
                elif mm := self.BLOCK_START.match(line):
                    self.block_opened(mm.group('name'), mm.group('params'), line_num)
                else:
                    self.raw_text(line, line_num)

            final_text, final_block_start = self.text_up_to_now() or (None, None)
            if final_text:
                final_block = TextBlock('<final>', final_block_start)
                final_block.text(final_text, final_block_start)
                self.sections.append(Section(final_block_start, self.last_section_title, final_block))

            self.prune_empty_sections()

            return RichDoc(path_or_ident, self.front_matter, self.summary, self.sections)

    def raw_text(self, line, line_num):
        # Feed text to block if one is open, otherwise to body buffer
        if self.current_block:
            self.current_block.text(line, line_num)
            return

        self.body_lines.append((line_num, line))

    def text_up_to_now(self) -> Optional[Tuple[str, int]]:
        if not self.body_lines:
            return None

        text = ''.join([line for _, line in self.body_lines])
        start_line, _ = self.body_lines[0]
        return (text, start_line)

    def prune_empty_sections(self):
        self.sections = [Section(ln, title, block)
                         for (ln, title, block) in self.sections
                         if not (isinstance(block, TextBlock) and self.ALL_BLANKS.match("".join(block.body)))] # TODO: Inefficient join


    def block_closed(self, line_num: int):
        if not self.current_block:
            self.logger.log_error("Block close found before block was opened", line_num=line_num)
            return

        self.sections.append(Section(
            self.current_block.starting_line,
            f'<{self.current_block.__class__.__name__}>',
            self.current_block
        ))

        try:
            self.current_block.close()
        except Exception as e:
            # TODO: This may have precise location information
            self.logger.exception(e, "Could not parse block body", line_num=self.current_block.starting_line)
        finally:
            self.current_block = None
            self.last_section_title = None

    def block_opened(self, block, params, line_num):
        # Wrap up current text and add as section
        section_text, start_line = self.text_up_to_now() or (None, None)
        self.clear_buf()

        if section_text:
            text_block = TextBlock(self.last_section_title, line_num)
            text_block.text(section_text, line_num)
            self.sections.append(Section(start_line, self.last_section_title, text_block))

        if self.current_block:
            block_str = "{block}({params})" if params else block
            self.logger.error(f"Opening new block {block_str} before closing previous one", line_num=line_num)
        self.current_block = self.create_block(block, params, line_num)

    def section_header(self, title, line, line_num):
        # If we're in a block, don't create sections
        if self.current_block:
            self.raw_text(line, line_num)
            return

        # Wrap up current text and add as section
        section_text, start_line = self.text_up_to_now() or (None, None)
        self.clear_buf()

        if section_text:
            text_block = TextBlock(self.last_section_title, line_num)
            text_block.text(section_text, line_num)
            self.sections.append(Section(start_line, self.last_section_title, text_block))

        # Include header as part of section body
        self.raw_text(line, line_num)

        self.last_section_title = title

    def frontmatter_delimiter(self, line_num):
        if self.current_block:
            if not isinstance(self.current_block, FrontMatterBlock): # Unlikely
                self.logger.log_error("Encountered front matter delimiter outside of a FrontMatterBlock", line_num=line_num)

            # Closing a block adds it to sections
            self.block_closed(line_num)
            # Now remove it from sections, it's special
            _, _, fm = self.sections.pop()
            self.front_matter = fm.front_matter
        else:
            if self.front_matter:
                self.logger.log_issue("Extra frontmatter delimiter encountered", line_number=line_num)

            # No need to wrap up preceding text, this is at document start
            self.current_block = FrontMatterBlock(line_num)

    def summary_closed(self, line_num):
        summary, _ = self.text_up_to_now() or ('', None)
        # NOTE: not calling clear_buf() - we want the text to remain
        self.raw_text('\n', line_num)
        self.summary = summary.strip()

    def clear_buf(self):
        self.body_lines = []

    def create_block(self, block, params, line_num) -> Block:
        return BlockRegistry.create_block(block, params, line_num)

if __name__ == "__main__":
    # doc = RichDoc.from_file(Path("content/a/grand-timeline.md"), sink)
    event =  Path("content/e/low/2025-04-06-low-2.md")
    evt = RichDocParser().parse_file(event)
    # belt =  RichDoc.from_file(Path("content/c/ppw-championship.md"), sink)
    breakpoint()

...
