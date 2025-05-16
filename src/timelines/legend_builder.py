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
        return pat.Rectangle((0, 0), 0.5, 0.5, color=self.colors.lookup(colorspec))

    def add_explicit(self, row: list[Any]):
        # Add a legend item from a CSV row
        # TODO
        pass

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

    def add(self, text):
        if text in self.legend_items:
            return

        self.legend_items[text] = (self.renderer(text), self.make_patch(text))

    def legend(self):
        keys_patches = self.legend_items.values()
        labels = [kp[0] for kp in keys_patches]
        patches = [kp[1] for kp in keys_patches]
        return (labels, patches)
