from pathlib import Path
from mistletoe import Document
from mistletoe.markdown_renderer import MarkdownRenderer

from parse import blocks
from guards.main.base import Base
from guards.main.markup import find_links

class ContentLinks(Base):
    # TODO: Autocorrectable
    # TODO: Reject image links ![](path/to/image). This may be another class.

    # NOTE: no accepts_xxx methods - this runs on everything.

    def validate_text(self, block: blocks.TextBlock):
        with MarkdownRenderer() as renderer:
            doc = Document(''.join(block.body)) # Important to properly count lines
            for link, linenum in find_links(doc):
                # Only handle links of the form [label](target)
                if link.dest_type != 'uri':
                    continue

                formatted_link = "".join(renderer.render(link)).rstrip()

                if link.target.startswith('content/'):
                    self.report_content_link(formatted_link, linenum, block.starting_line)
                elif link.target.startswith('@') and self.destination_file_missing(link.target):
                    self.report_missing_target(formatted_link, linenum, block.starting_line)

    def report_content_link(self, formatted_link: str, relative_linenum: int, starting_line: int):
        self.log_error(f"`{formatted_link}` links to content/. Replace the target to start with `@` instead.", line_number=starting_line + relative_linenum)

    def report_missing_target(self, formatted_link: str, relative_linenum: int, starting_line: int):
        self.log_error(f"`{formatted_link}` links to a non-existent file. The filename may be misspelled, or not created yet.", line_number=starting_line + relative_linenum)

    def destination_file_missing(self, link_target: str) -> bool:
        target, _, _ = link_target.partition('#')
        path = Path('content') / target[2:] # Strip @/
        return not path.exists()
