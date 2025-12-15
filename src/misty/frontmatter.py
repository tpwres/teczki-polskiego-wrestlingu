from mistletoe.block_token import BlockToken
from mistletoe.span_token import RawText
import tomllib

class Frontmatter(BlockToken):
    def __init__(self, matched_text):
        lines = matched_text
        self.children = (RawText('\n'.join(lines)),)

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

    @staticmethod
    def parse_frontmatter(content):
        return tomllib.loads(content)
