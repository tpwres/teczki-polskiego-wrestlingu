from json import JSONEncoder
from collections import Counter
import tomllib
import re
from typing import TextIO

invalid_names_re = re.compile(r'^([?]+|TBA|Unknown\d*)$')

frontmatter_re = re.compile(r'''
    ^[+]{3}$ # Frontmatter delimiter: three pluses on a standalone line
    (?P<frontmatter>(?:.|\n)*) # Frontmatter content
    ^[+]{3}$ # Another delimiter
''', re.VERBOSE | re.MULTILINE)

block_re = re.compile(r'''
    ^\{%\s+                # Opening {% and whitespace
    (?P<keyword>\w+)       # keyword (usually card)
    \([^)]*\)              # Open parentheses, any content, closing parentheses
    \s+                    # Followed by whitespace
    %\}$                   # Closing %}
    (?P<content>(?:\n|.)*) # Block content
    ^\{%\s+                # Opening {% and whitespace
    end\s+                 # End keyword, whitespace
    %\}$                   # Closing %}
''', re.VERBOSE | re.MULTILINE)

def accepted_name(name):
    """
    Return false if name is a placeholder, otherwise true.
    """
    return invalid_names_re.match(name) == None

def extract_front_matter(text):
    match frontmatter_re.match(text.lstrip()):
        case re.Match() as m:
            return m.group('frontmatter').strip()
        case _:
            raise ValueError("Could not find frontmatter block")

def parse_front_matter(text):
    return tomllib.loads(extract_front_matter(text))

def strip_blocks(text: str) -> str:
    passthrough_keywords = {'timeline'}

    def replace_block(matchobj):
        if matchobj.group('keyword') in passthrough_keywords:
            return f"\n{matchobj.group('content')}\n"
        else:
            return "\n" * matchobj.group('content').count("\n")

    body = frontmatter_re.sub(lambda matchobj: "\n" * matchobj.group('frontmatter').count("\n"), text)
    return block_re.sub(replace_block, body)

class RichEncoder(JSONEncoder):
    def default(self, o):
        match o:
            case set():
                return list(o)
            case Counter():
                return dict(o)
            case _:
                return super().default(o)

class SkipComments:
    """
    Wraps an IO object, and provides iteration over its lines.
    Skips lines that start with a comment marker (#)
    """
    def __init__(self, io: TextIO):
        self.io = iter(io.readlines())

    def __iter__(self):
        return self

    def __next__(self) -> str:
        while True:
            line = next(self.io)
            if not line.startswith('#'):
                break

        return line
