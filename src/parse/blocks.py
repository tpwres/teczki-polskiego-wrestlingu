from functools import partial
from typing import ClassVar, Any, Optional
import yaml
import tomllib
from textwrap import shorten

class BlockRegistry:
    block_classes: ClassVar[dict[Optional[str], type]] = {}

    @classmethod
    def register_block(cls, block_name):
        def decorate(cls, name, block_class):
            cls.block_classes[name] = block_class
            return block_class

        return partial(decorate, cls, block_name)

    @classmethod
    def create_block(cls, block, params, line_num):
        factory = BlockRegistry.block_classes.get(block)
        if factory:
            return factory(params, line_num)

        factory = BlockRegistry.block_classes.get(None)
        if factory:
            return factory(params, line_num)

        raise DocError(f"Unsupported block type {block}")

register_block = BlockRegistry.register_block

class Block:
    "Basic block that collects text without processing it."
    starting_line: int
    body: list[str]
    params: Optional[str]

    def __init__(self, params: Optional[str], line_num: int):
        self.params = params
        self.starting_line = line_num

        self.body = []

    def close(self):
        pass

    def text(self, line, line_num):
        self.body.append(line)

class TextBlock(Block):
    def __repr__(self):
        full_text = ''.join(self.body)
        return f'<TextBlock@{self.starting_line} {shorten(full_text, 40)}>'

    @property
    def title(self):
        return self.params


@register_block('card')
class CardBlock(Block):
    raw_card: list[Any]

    def __init__(self, params, line_num):
        super().__init__(params, line_num)
        self.raw_card = []

    def close(self):
        card_text = ''.join(self.body)
        self.body = []
        try:
            self.raw_card = yaml.safe_load(card_text)
        except yaml.YAMLError as e:
            raise ParseError(e)

@register_block('free_card')
class FreeCardBlock(Block):
    raw_card: list[Any]

    def __init__(self, params, line_num):
        super().__init__(params, line_num)
        self.raw_card = []

    def close(self):
        card_text = '\n'.join(self.body)
        try:
            self.raw_card = yaml.safe_load(card_text)
        except yaml.YAMLError as e:
            raise ParseError(e)
        self.body = []

@register_block('timeline')
class TimelineBlock(Block):
    pass

@register_block(None) # Register as fallback factory
class UnknownBlock(Block):
    pass

# No need to register, RichDoc uses it explicitly
class FrontMatterBlock(Block):
    def __init__(self, line_num):
        super().__init__(None, line_num)

    def close(self):
        fm_text = '\n'.join(self.body)
        self.front_matter = tomllib.loads(fm_text)
        self.body = []
