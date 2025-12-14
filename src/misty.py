import sys
import re
import mistletoe, mistletoe.ast_renderer
from mistletoe.ast_renderer import AstRenderer
from mistletoe.base_renderer import BaseRenderer
from mistletoe import span_token, block_token
import tomllib

class Frontmatter(block_token.BlockToken):
    def __init__(self, matched_text):
        lines = matched_text
        self.children = (span_token.RawText('\n'.join(lines)),)

    @property
    def content(self):
        return self.children[0].content

    @classmethod
    def start(cls, line):
        if not line.startswith('+++'):
            return False

        return True

    @classmethod
    def read(cls, lines):
        next(lines) # Because the first line is peek()ed
        buf = []
        for line in lines:
            if line.startswith('+++'):
                break

            buf.append(line.strip())

        return buf

class LiquidBlock(block_token.BlockToken):
    head_pattern = re.compile(r'''
      \{%
      (
        \s*
        (\S+)\(
          [^)]*
        \)
        \s*
      )
      %\}
    ''', re.VERBOSE)
    repr_attributes = block_token.BlockToken.repr_attributes + ("head",)

    def __init__(self, matched_lines):
        lines, (expr, head) = matched_lines
        self.expr = expr
        self.head = head
        self.children = (span_token.RawText('\n'.join(lines)),)

    @property
    def content(self):
        return self.children[0].content

    @classmethod
    def start(cls, line):
        if not line.startswith('{%'):
            return False

        matchobj = cls.head_pattern.match(line)
        if not matchobj:
            return False

        expr = matchobj.group(1)
        head = matchobj.group(2)
        cls._block_info = (expr, head)
        return True

    @classmethod
    def read(cls, lines):
        next(lines)
        buf = []
        for line in lines:
            if line.startswith('{% end %}'):
                break

            buf.append(line.strip())

        return buf, cls._block_info


class LiquidExpr(span_token.SpanToken):
    parse_inner = False
    pattern = re.compile(r'''
      \{\{
      (
        \s*
        (\S+)\(
          [^)]+
        \)
        \s*
      )
      \}\}
    ''', re.VERBOSE)
    repr_attributes = span_token.SpanToken.repr_attributes + ("head",)

    def __init__(self, matchobj):
        self.content = matchobj.group(self.parse_group)
        self.head = matchobj.group(2)

class LiquidSpan(span_token.SpanToken):
    parse_inner = True
    parse_group = 3
    precedence = 4
    repr_attributes = span_token.SpanToken.repr_attributes + ("head",)
    pattern = re.compile(r'''
      \{%
      (
        \s*
        (\S+)\(
          [^)]+
        \)
        \s*
      )
      %\}
     (.*?)
     \{%\s+end\s+%\}
    ''', re.VERBOSE)

    def __init__(self, matchobj):
        self.head = matchobj.group(2)


class RichRenderer(BaseRenderer):
    def __init__(self):
        super().__init__(LiquidBlock, Frontmatter, LiquidExpr, LiquidSpan)

    # These just need to exist, not necessarily do anything
    def render_liquid_expr(self, token):
        pass

    def render_liquid_span(self, token):
        pass

    def render_liquid_block(self, token):
        pass

    def render_frontmatter(self, token):
        pass

def parse_frontmatter(content):
    return tomllib.loads(content)

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
                yield kls, (current_line, None), (parse_frontmatter(content),)
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
        with RichRenderer() as renderer:
            doc = mistletoe.Document(fp)

            # Starting from doc which is an element by itself, walk recursively through children.
            # Keep current line number. For Paragraphs, track linebreaks and increase it.
            yield from walk_toplevel(doc, 1)
            # doc has .footnotes, but with no line numbers, and the markup nodes are consumed silently
            # they are already resolved into links

def main():
    if len(sys.argv) > 1:
        stream = open(sys.argv[1], 'r')
    else:
        stream = sys.stdin

    for tok in emit_tokens_with_lines(stream):
        kls, (row, col), content = tok
        colstr = ':01' if col is None else f':{col:02d}'
        print(f"{row}{colstr} | {kls} {content}")

if __name__ == "__main__":
    main()
