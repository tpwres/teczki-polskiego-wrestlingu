from mistletoe import Document
from mistletoe.base_renderer import BaseRenderer
from mistletoe.block_token import BlockToken
from mistletoe.span_token import SpanToken, Link
from typing import Tuple, Generator

LinkGenerator = Generator[
    Tuple[Link, int],
    None,
    None
]

def find_links(element: SpanToken|BlockToken, line_number:int=0) -> LinkGenerator:
    """Walk the AST recursively, but work on objects and not unpacked dicts from get_ast"""
    if hasattr(element, 'line_number'):
        line_number = element.line_number

    match element:
        case Link() as link:
            yield (link, line_number)
        case BlockToken(children=children) | SpanToken(children=children) if children:
            for child in children:
                yield from find_links(child, line_number)

def parse_link(link_text: str) -> Tuple[str, str]:
    doc = Document(link_text)
    renderer = BaseRenderer()
    for link, line_number in find_links(doc):
        label = renderer.render(link)
        target = link.target
        return (label, target)

if __name__ == "__main__":
    breakpoint()
