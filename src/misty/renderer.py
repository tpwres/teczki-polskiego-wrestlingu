from mistletoe.base_renderer import BaseRenderer
from .frontmatter import Frontmatter
from .liquid import LiquidExpr, LiquidContentBlock, DataBlock, LiquidSpan

class NoopRenderer(BaseRenderer):
    def __init__(self):
        super().__init__(LiquidContentBlock, DataBlock, Frontmatter, LiquidExpr, LiquidSpan)

    # These just need to exist, not necessarily do anything
    def render_liquid_expr(self, token):
        pass

    def render_liquid_span(self, token):
        pass

    def render_liquid_content_block(self, token):
        pass

    def render_data_block(self, token):
        pass

    def render_frontmatter(self, token):
        pass
