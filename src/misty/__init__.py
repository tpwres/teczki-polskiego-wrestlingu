import mistletoe, mistletoe.ast_renderer
from mistletoe.ast_renderer import AstRenderer
from mistletoe.base_renderer import BaseRenderer
from mistletoe import span_token, block_token

from .frontmatter import Frontmatter
from .liquid import LiquidExpr, LiquidBlock, LiquidSpan
from .renderer import NoopRenderer

def walk_nested(elem, line_num):
    row, col = line_num, 1
    for el in elem.children:
        tp = type(el).__name__
        if hasattr(el, 'line_number'):
            row = el.line_number
        match el:
            case span_token.LineBreak():
                row += 1
                col = 1
            case span_token.RawText(content=content):
                yield 'Text', (row, col), (content,)
                col += len(content)
            case span_token.Link(target=target, children=[span_token.RawText(content=content)]):
                yield tp, (row, col), (target, content)
                col += len(target) + len(content) + 4
            case span_token.SpanToken(children=[span_token.RawText(content=content)]):
                yield tp, (row, col), (content,)
                col += len(content)
            case LiquidExpr(content=content, head=head):
                yield f'={head}', (row, col), (content,)
                col += len(content) + 4
            case block_token.ListItem(children=children):
                # prepend contains the additional list margin
                for tt, (r, c), data in walk_nested(el, row):
                    yield tt, (r, c + el.prepend), data
            case span_token.SpanToken(children=nested):
                yield tp, (row, col), (content,)
                col += len(content)
            case block_token.Paragraph():
                yield from walk_nested(el, row)
            case _:
                raise ValueError(f"Unhandled element {el}")

# The two functions aren't that different and could be folded into one
# Better yet, a class could be built for better row,col tracking.
# However, this is very similar to the mistletoe Renderer class, but that specifically emits another document (a str), does not yield tokens
def walk_toplevel(elem, line_num):
    current_line = line_num

    for el in elem.children:
        current_line = el.line_number
        kls = type(el).__name__
        match el:
            case Frontmatter(content=content):
                yield kls, (current_line, None), (Frontmatter.parse_frontmatter(content),)
            case LiquidBlock(head='card', content=content):
                yield '!Card', (current_line, 1), (content,)
            case LiquidBlock(content=content, head=head):
                yield f'!{head}', (current_line, None), (content)
            case block_token.Heading(children=[span_token.RawText(content=content)], level=level):
                yield 'Heading', (current_line, 1), (level, content)
            case block_token.Paragraph():
                yield from walk_nested(el, current_line)
            case block_token.List():
                # yield 'List', (current_line, None), ()
                for kls, (r, c), data in walk_nested(el, current_line):
                    yield kls, (r, c), data
                    current_line = r
                # yield '/List', (current_line, None), ()
            case _:
                # yield kls, (current_line, None), el
                raise ValueError(f"Unhandled toplevel element {el}")

def emit_tokens_with_lines(stream):
    with stream as fp:
        with NoopRenderer() as renderer:
            doc = mistletoe.Document(fp)

            # Starting from doc which is an element by itself, walk recursively through children.
            # Keep current line number. For Paragraphs, track linebreaks and increase it.
            yield from walk_toplevel(doc, 1)
            # doc has .footnotes, but with no line numbers, and the markup nodes are consumed silently
            # they are already resolved into links
