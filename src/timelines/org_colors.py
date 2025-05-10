from pathlib import Path
from typing import Any
import tomllib
import re
import matplotlib.colors as mcolors

def load_org_colors_from_config():
    config_path = Path(__file__).parent / '../..' / 'config.toml'
    with config_path.resolve().open('rb') as fp:
        project_config = tomllib.load(fp)
        styles = project_config['extra']['org_styles']
        return {key: org['bg'] for key, org in styles.items()}

LINE_STYLES = ('solid', 'dashed', 'dashdot', 'dotted')

class OrgColors:
    def __init__(self):
        # TODO: Some handling for #000 as the 'default' color, and color overrides
        self.colors = {}
        self.colors.update(load_org_colors_from_config())
        self.custom_colors = {}

    # Supported hatches: | for vertical stripes and /, \ for slanted ones
    # Doubled variants give more density
    HATCH_RE = re.compile(r'''
        (?<=\w)( # Assert we're starting after a letter
          //   | /    | # Double and single slash
          \\\\ | \\   | # Double and single backslash, with escaping
          \|   | \|\|   # Pipe and double pipe, with escaping
        )(?=[\w!#]) # Ending before symbols that can start a color
        ''', re.X)

    def lookup(self, color: str) -> Any:
        if color.startswith('!'):
            name = color[1:]
            return mcolors.CSS4_COLORS[name]
        elif color.startswith('#') and len(color) == 7: # RGB as-is
            return color

        return self.colors.get(color, '#FF00FF')

    def add_custom(self, name: str, spec: str):
        self.custom_colors[name] = spec

    def line(self, colorspec: str) -> dict[str, Any]:
        # Like paint() below but for lines
        # colorspec is a single color, either org hex or named
        # which can be followed space-separated thickness and style, both optional
        if colorspec == '':
            return {} # Matplotlib defaults

        color, *rest = colorspec.split()
        attrs: dict[str, Any] = {'color': self.lookup(color)}

        match rest:
            case []:
                pass
            case [thickness, style] if style in LINE_STYLES:
                attrs['linewidths'] = [float(thickness)]
                attrs['linestyles'] = [style]
            case [style] if style in LINE_STYLES:
                attrs['linestyles'] = [style]
            case [thickness]:
                attrs['linewidths'] = [float(thickness)]
            case _:
                raise ValueError(f"Unrecognized line style {rest}")

        return attrs


    def paint(self, colorspec: str) -> dict[str, Any]:
        # A custom color must first be resolved into its definition
        colorspec = self.custom_colors.get(colorspec, colorspec)

        specs = OrgColors.HATCH_RE.split(colorspec)
        match specs:
            case [single]:
                return {'color': self.lookup(single)}
            case [color1, pattern, color2]:
                return {
                    'facecolor': self.lookup(color1),
                    'edgecolor': self.lookup(color2),
                    'hatch': pattern
                }
            case _:
                raise ValueError(f"Unsupported color spec {colorspec}")


    @staticmethod
    def split_orgs(text: str) -> list[str]:
        """Public method for other classes to use for parsing the org colors"""
        return OrgColors.HATCH_RE.split(text)
