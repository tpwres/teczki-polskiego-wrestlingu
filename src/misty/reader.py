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
        return self

    def cr(self):
        self.col = 1
        return self

    @property
    def pos(self) -> (int, int):
        return (self.row, self.col)

    @property
    def bol(self) -> (int, int):
        return (self.row, 1)

    def wrap_block(self, name, block_node, depth, *data):
        yield f'{name}Start', self.bol, data
        yield from self.walk_nested(block_node, depth)
        yield f'{name}End', self.bol, data

    def handle_list_item(self, item_node, depth):
        # prepend contains the additional list margin
        margin = item_node.prepend
        for token, (row, col), data in self.walk_nested(item_node, depth):
            yield token, (row, col + margin), data

    def handle_link(self, subnode, depth):
        match subnode:
            case span_token.Link(target=target, children=[span_token.RawText(content=content)]):
                yield 'Link', self.pos, (target, content)
                self.advance(cols=len(target) + len(content) + 4)
            case span_token.Link(target=target, children=children):
                yield from self.wrap_block('Link', subnode, depth+1, target)

    def handle_liquid_content(self, subnode, head, depth):
        yield 'ContentBlockStart', self.bol, (head,)
        start = self.row
        for token, (inner_row, col), data in self.walk_nested(subnode, depth+1):
            # Inside a block token like this, line numbers restart in inner parsing
            yield token, (start + inner_row, col), data
        self.row = start + inner_row + 1
        yield 'ContentBlockEnd', self.bol, (head,)

    def walk_nested(self, node, depth=1):
        for subnode in node.children:
            if hasattr(subnode, 'line_number'):
                self.row = subnode.line_number
            nodename = type(subnode).__name__

            match subnode:
                case span_token.LineBreak():
                    self.advance(rows=1).cr()
                case span_token.Link():
                    yield from self.handle_link(subnode, depth)
                case block_token.List():
                    yield from self.wrap_block('List', subnode, depth+1)
                case block_token.ListItem(children=children):
                    yield from self.handle_list_item(subnode, depth+1)
                case Frontmatter(content=content):
                    yield nodename, self.bol, (Frontmatter.parse_frontmatter(content),)
                case DataBlock(head='card', content=card):
                    yield 'Card', self.bol, (card,)
                case LiquidContentBlock(head=head):
                    yield from self.handle_liquid_content(subnode, head, depth)
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
                case span_token.SpanToken(children=[span_token.RawText(content=content)]):
                    # Any other inline node with just rawtext, e.g. InlineCode
                    yield nodename, self.pos, (content,)
                    self.advance(cols=len(content))
                # Emphasis, has some issues when nested in lists
                case span_token.SpanToken(children=children, delimiter=delim):
                    offset = len(delim)
                    yield f'<{nodename}', self.pos, ()
                    for token, (row, col), data in self.walk_nested(subnode, depth+1):
                        yield token, (row, col + offset), data
                    yield f'>{nodename}', self.pos, ()
                    self.advance(cols=2*offset)
                case _:
                    raise ValueError(f"Unhandled node {subnode}")
