import re
from typing import Any, cast

from mistletoe.markdown_renderer import MarkdownRenderer, BlankLine
from parse import blocks
from guards.main.base import Base

from mistletoe import Document
import mistletoe.token as t

class BadgesValid(Base):
    """Looks for org_badge markup in text and tries to catch incorrect use."""

    def validate_text(self, text: blocks.TextBlock):
        with MarkdownRenderer():
            doc = Document(''.join(text.body))
            self.line_number = text.starting_line
            self.walk(doc)

    def walk(self, node: t.Token):
        for child in node.children or []:
            match child:
                case BlankLine():
                    self.line_number += 1
                case parent if parent.children:
                    return self.walk(parent)
                case token if hasattr(token, 'content') and  'org_badge(' in cast(Any, token).content:
                    return self.check_badge_code(token)

    def check_badge_code(self, token: t.Token):
        content = cast(Any, token).content
        if not (content.startswith('{{') and content.endswith('}}')):
            self.logger.log_error("Badge code must start and end with double braces `{{ org_badge(...) }}`")

        if not (content.count('(') == content.count(')') == 1):
            self.logger.log_error("Badge code must have exactly one opening and one closing parenthesis")

        params = re.search(r"org_badge\((\w+)=([^)]+)\)", content)
        if not params:
            self.logger.log_error("Badge code must follow format: org_badge(org='name') or org_badge(orgs=['name1', 'name2'])")
            return

        # NOTE: Doubled braces because of the f-string
        message = None
        match (params.group(1), params.group(2)):
            case ('org', text) if text_is_quoted(text) and ',' not in text:
                pass
            case ('org', array) if is_list(array):
                message = f"Badge code must use orgs= for multiple orgs `{{{{ org_badge(orgs={array}) }}}}`"
            case ('org', text):
                message = f"Badge code must surround org name with quotes `{{{{ org_badge(orgs='{text}') }}}}"
            case ('orgs', array) if is_list(array):
                pass
            case ('orgs', text) if text_is_quoted(text):
                message = f"Badge code must use org= for single org `{{{{ org_badge(org={text}) }}}}`"
            case ('orgs', text) if ',' in text:
                names = ', '.join(f"'{name}'" for name in text.split(','))
                message = f"Badge code must use orgs= with an array of quoted org names `{{{{ org_badge(orgs=[{names}]) }}}}`"
            case ('orgs', text):
                message = f"Badge code must use orgs= with an array of quoted org names `{{{{ org_badge(orgs=['{text}']) }}}}`"

        if message:
            self.logger.log_error(message, line_number=self.line_number)

def text_is_quoted(text: str) -> bool:
    return (text.startswith("'") and text.endswith("'")) or (text.startswith('"') and text.endswith('"'))

def is_list(text: str) -> bool:
    return text.startswith('[') and text.endswith(']') and all(text_is_quoted(item.strip()) for item in text[1:-1].split(','))
