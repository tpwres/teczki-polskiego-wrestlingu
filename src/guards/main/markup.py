from typing import Generator, Tuple, Any, cast
from mistletoe.token import Token
from mistletoe.block_token import BlockToken
from mistletoe.span_token import SpanToken, Link

def find_links(element: Token, line_number: int = 0) -> Generator[Tuple[Link, int], None, None]:
    """Walk the AST recursively, but work on objects and not unpacked dicts from get_ast"""
    try:
        line_number = cast(Any, element).line_number
    except AttributeError:
        pass

    match element:
        case Link() as link:
            yield (link, line_number)
        case BlockToken(children=children) | SpanToken(children=children) if children:
            for child in children:
                yield from find_links(child, line_number)
