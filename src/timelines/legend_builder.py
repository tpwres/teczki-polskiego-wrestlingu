from .org_colors import OrgColors
from .stripe import Stripe
from typing import Any, Callable
from matplotlib import patches as pat

split_orgs = OrgColors.split_orgs

class LegendBuilder:
    def __init__(self, colors: OrgColors, renderer: Callable[[str], Any]):
        # it's tempting to make this generic: renderer is Callable[[str], T] and legend_items is a dict[str, T]
        # Overkill though
        self.colors = colors
        self.renderer = renderer
        self.legend_items: dict[str, Any] = {}


    def make_patch(self, colorspec):
        # return pat.Rectangle((0, 0), 0.5, 0.5, color=self.colors.lookup(colorspec))
        return pat.Rectangle((0, 0), 0.5, 0.5, **self.colors.paint(colorspec))

    def add_stripe(self, stripe: Stripe):
        # Add a legend item from a stripe
        # We look at the stripe's org property, extract only the org names from there
        specs = split_orgs(stripe.org)
        for item in specs:
            if self.acceptable(item):
                self.add(item)

    def acceptable(self, text):
        if text.startswith('!') or text.startswith('#'): # Ignore named and RGB
            return False

        if text.isalpha():
            return True

    def add(self, symbol):
        if symbol in self.legend_items:
            return

        self.legend_items[symbol] = (self.renderer(symbol), self.make_patch(symbol))

    def add_explicit(self, symbol: str, descr: str):
        if symbol in self.legend_items:
            return

        self.legend_items[symbol] = (self.render_custom(descr), self.make_patch(symbol))

    def render_custom(self, text):
        # TODO
        return text

    def legend(self):
        keys_patches = self.legend_items.values()
        labels = [kp[0] for kp in keys_patches]
        patches = [kp[1] for kp in keys_patches]
        return (labels, patches)
