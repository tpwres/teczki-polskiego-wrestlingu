from mistletoe import block_token, span_token

from .frontmatter import Frontmatter
from .liquid import LiquidExpr, LiquidContentBlock, DataBlock, LiquidSpan

class Reader:
    def __init__(self, document):
        self.document = document

    def walk(self):
        yield from self.walk_nested(self.document)

    def walk_nested(self, node, row=1, col=1):
        for subnode in node.children:
            if hasattr(subnode, 'line_number'):
                row = subnode.line_number
            nodename = type(subnode).__name__

            # NOTE: putting row, col in ivars may help clean up this code
            match subnode:
                case span_token.LineBreak():
                    row += 1
                    col = 1
                case span_token.Link(target=target, children=[span_token.RawText(content=content)]):
                    yield nodename, (row, col), (target, content)
                    col += len(target) + len(content) + 4
                case block_token.List():
                    yield 'ListStart', (row, 1), ()
                    for kls, (r, c), data in self.walk_nested(subnode, row, col):
                        yield kls, (r, c), data
                        row = r
                    yield 'ListEnd', (row, 1), ()
                case block_token.ListItem(children=children):
                    # prepend contains the additional list margin
                    for kls, (r, c), data in self.walk_nested(subnode, row, col):
                        yield kls, (r, c + subnode.prepend), data
                case Frontmatter(content=content):
                    yield nodename, (row, 1), (Frontmatter.parse_frontmatter(content),)
                case DataBlock(head='card', content=card):
                    yield 'Card', (row, 1), (card,)
                case LiquidContentBlock(head=head):
                    yield 'ContentBlockStart', (row, 1), (head,)
                    yield from self.walk_nested(subnode)
                    yield 'ContentBlockEnd', (row, 1), (head,)
                # case LiquidContentBlock(head=head, content=content):
                #     yield f'{head}', (row, 1), (content,)
                case LiquidExpr(content=content, head=head):
                    yield f'={head}', (row, col), (content,)
                    col += len(content) + 4
                case block_token.Heading(children=[span_token.RawText(content=raw)], level=level):
                    yield 'Heading', (row, 1), (level, raw)
                case block_token.Paragraph(): # Should be any block token with children?
                    yield from self.walk_nested(subnode, row)
                # Must be above other generic span tokens
                case span_token.RawText(content=content):
                    yield 'Text', (row, col), (content,)
                    col += len(content)
                # For Emphasis, if needed, the type is in .delimiter (_|*|~)
                case span_token.SpanToken(children=[span_token.RawText(content=content)]):
                    # Any unhandled inline node with just rawtext
                    yield nodename, (row, col), (content,)
                    col += len(content)
                case span_token.SpanToken(children=children):
                    yield f'<{nodename}', (row, col), ()
                    for kls, (r, c), data in self.walk_nested(subnode, row, col):
                        yield kls, (r, c), data
                        row = r
                    yield f'>{nodename}', (row, col), ()
                case _:
                    breakpoint()
                    raise ValueError(f"Unhandled node {subnode}")


