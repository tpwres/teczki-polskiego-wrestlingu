from typing import Sequence
from pathlib import Path
from urllib.parse import urlparse, ParseResult
from misty.dsl import Rule, SingleMatch, Token, Message, Level, Fixable

def link_target_startswith_content(_tok, _pos, args):
    return args[0].startswith('content')

class ValidInternalLink(Rule):
    pattern = (SingleMatch(type='ZolaLink')
               | SingleMatch(type='Link',fn=link_target_startswith_content))

    def ignore(self, path: Path):
        return path.suffix != '.md'

    def process(self, token: Token) -> Optional[Token]:
        tp, (row, col), rest = token
        target, text, dest_type, label = self.unpack_link(rest)
        if target.startswith('content'):
            new_target = target.replace('content/', '@/')
            return [tp, (row, col), (new_target, text, dest_type, label)]

        return None # No changes

    def describe(self, token) -> Optional[List[Message]]:
        _, (row, col), rest = token
        target, text, dest_type, label = self.unpack_link(rest)
        full_link = self.render_link(target, text, dest_type, label)

        messages: List[Message] = []
        if target.startswith('content'):
            messages.append(
                Message(text=f'{full_link} links to content/. Replace the target to start with `@` instead',
                        location=(row, col),
                        level=Level.ERROR
                )
            )

        if target.startswith('@') and self.destination_file_missing(target):
            messages.append(
                Message(text=f'{full_link} links to a non-existent file. The filename may be misspelled or not created yet.',
                        location=(row, col),
                        level=Level.ERROR
                )
            )

        return messages or None

    @staticmethod
    def render_link(target, text, dest_type, label):
        if dest_type == 'full':
            return f'[{text}][{label}]'
        else:
            return f'[{text}]({target})'

    def destination_file_missing(self, link_target: str) -> bool:
        filename, _hash, _fragment = link_target.partition('#')
        # NOTE: user/parent class should provide a resolver?
        path = Path('content') / filename[2:] # Strip `@/`
        return not path.exists()

    def unpack_link(self, args) -> Tuple[str, str, str, Optional[str]]:
        match args:
            case (str(link_target), str(link_text)):
                return link_target, link_text, 'internal', None
            case (str(target), str(text), str(link_type), str(link_label)):
                return link_target, link_text, link_type, link_label

default_rules = (
    ValidInternalLink,
)
