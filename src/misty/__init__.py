import mistletoe, mistletoe.ast_renderer
from mistletoe import span_token, block_token

from .frontmatter import Frontmatter
from .renderer import NoopRenderer
from .reader import Reader

def emit_tokens_with_lines(stream):
    with stream as fp:
        with NoopRenderer() as renderer:
            doc = mistletoe.Document(fp)
            reader = Reader(doc)

            # Starting from doc which is an element by itself, walk recursively through children.
            # Keep current line number. For Paragraphs, track linebreaks and increase it.
            yield from reader.walk()
            # doc has .footnotes, but with no line numbers, and the markup nodes are consumed silently
            # they are already resolved into links
