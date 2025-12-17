from mistletoe import block_token, span_token

from .frontmatter import Frontmatter
from .liquid import LiquidExpr, LiquidContentBlock, DataBlock, LiquidSpan

class Reader:
    def __init__(self, document):
        self.document = document
        self.row: int = 1
        self.col: int = 1

    def walk(self):
        yield from self.walk_nested(self.document)

    def advance(self, *, rows=0, cols=0):
        self.row += rows
        self.col += cols

    def cr(self):
        self.col = 1

    @property
    def pos(self) -> (int, int):
        return (self.row, self.col)

    @property
    def bol(self) -> (int, int):
        return (self.row, 1)

    def walk_nested(self, node, depth=1):
        for subnode in node.children:
            if hasattr(subnode, 'line_number'):
                self.row = subnode.line_number
            nodename = type(subnode).__name__

            match subnode:
                case span_token.LineBreak():
                    self.advance(rows=1)
                    self.cr()
                case span_token.Link(target=target, children=[span_token.RawText(content=content)]):
                    yield nodename, self.pos, (target, content)
                    self.advance(cols=len(target) + len(content) + 4)
                case block_token.List():
                    yield 'ListStart', self.bol, ()
                    # for kls, (r, c), data in self.walk_nested(subnode):
                    #     yield kls, (r, c), data
                    yield from self.walk_nested(subnode, depth+1)
                    yield 'ListEnd', self.bol, ()
                case block_token.ListItem(children=children):
                    # prepend contains the additional list margin
                    for kls, (r, c), data in self.walk_nested(subnode, depth+1):
                        yield kls, (r, c + subnode.prepend), data
                case Frontmatter(content=content):
                    yield nodename, self.bol, (Frontmatter.parse_frontmatter(content),)
                case DataBlock(head='card', content=card):
                    yield 'Card', self.bol, (card,)
                case LiquidContentBlock(head=head):
                    yield 'ContentBlockStart', self.bol, (head,)
                    yield from self.walk_nested(subnode, depth+1)
                    yield 'ContentBlockEnd', self.bol, (head,)
                case LiquidExpr(content=content, head=head):
                    yield f'={head}', self.pos, (content,)
                    self.advance(cols=len(content) + 4)
                case block_token.Heading(children=[span_token.RawText(content=raw)], level=level):
                    yield 'Heading', self.bol, (level, raw)
                    self.cr()
                case block_token.Paragraph(): # Should be any block token with children?
                    yield from self.walk_nested(subnode, depth+1)
                    self.cr()
                # Must be above other generic span tokens
                case span_token.RawText(content=content):
                    yield 'Text', self.pos, (content,)
                    self.advance(cols=len(content))
                # For Emphasis, if needed, the type is in .delimiter (_|*|~)
                case span_token.SpanToken(children=[span_token.RawText(content=content)]):
                    # Any unhandled inline node with just rawtext
                    yield nodename, self.pos, (content,)
                    self.advance(cols=len(content))
                case span_token.SpanToken(children=children):
                    yield f'<{nodename}', self.pos, ()
                    for kls, (r, c), data in self.walk_nested(subnode, depth+1):
                        yield kls, (r, c), data
                        self.row = r
                    yield f'>{nodename}', self.pos, ()
                case _:
                    raise ValueError(f"Unhandled node {subnode}")


