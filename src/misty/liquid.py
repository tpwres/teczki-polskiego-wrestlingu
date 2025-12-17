import re
from mistletoe.block_token import BlockToken, tokenize
from mistletoe.span_token import RawText, SpanToken

class LiquidExpr(SpanToken):
    """
    Inline-form zola/liquid function/macro call {{ func_or_macro() }}.
    """
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
    repr_attributes = SpanToken.repr_attributes + ("head",)

    def __init__(self, matchobj):
        self.content = matchobj.group(self.parse_group)
        self.head = matchobj.group(2)

class LiquidSpan(SpanToken):
    """
    Span-form zola/liquid function/macro call {% macro() %}...content...{% end %}, when
    used inside a paragraph.
    """
    parse_inner = True
    parse_group = 3
    precedence = 4
    repr_attributes = SpanToken.repr_attributes + ("head",)
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

class LiquidBlock(BlockToken):
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
    repr_attributes = BlockToken.repr_attributes + ("head",)

    def __init__(self, matched_lines):
        lines, (expr, head) = matched_lines
        self.expr = expr
        self.head = head

    @classmethod
    def start(cls, line):
        if not line.startswith('{%'):
            return False

        matchobj = cls.head_pattern.match(line)
        if not matchobj:
            return False

        expr = matchobj.group(1)
        head = matchobj.group(2)
        if head not in cls.allowed_heads:
            return False
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

class DataBlock(LiquidBlock):
    """
    Block zola/liquid function/macro call {% macro() %}...content...{% end %}, where head and end
    are on standalone lines. Cannot be used in a paragraph. Content is NOT parsed.
    """
    allowed_heads = ('card',)

    def __init__(self, matched_lines):
        super().__init__(matched_lines)
        lines, _ = matched_lines
        self.children = (RawText('\n'.join(lines)),)

    @property
    def content(self):
        return self.children[0].content


class LiquidContentBlock(LiquidBlock):
    """
    Block zola/liquid function/macro call {% macro() %}...content...{% end %}, where head and end
    are on standalone lines. Cannot be used in a paragraph. Content is parsed as Markdown.
    """
    allowed_heads = ('timeline',)

    def __init__(self, matched_lines):
        super().__init__(matched_lines)
        lines, _ = matched_lines
        # Necessary for tokenize() to work correctly
        lines = [line if line.endswith('\n') else '{}\n'.format(line) for line in lines]
        self.children = tokenize(lines)
