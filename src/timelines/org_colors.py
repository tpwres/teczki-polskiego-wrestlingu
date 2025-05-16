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

class OrgColors:
    def __init__(self):
        # TODO: Some handling for #000 as the 'default' color, and color overrides
        self.colors = {}
        self.colors.update(load_org_colors_from_config())

    # Supported hatches: | for vertical stripes and /, \ for slanted ones
    # Doubled variants give more density
    HATCH_RE = re.compile(r'''
        \b(
          //   | /    | # Double and single slash
          \\\\ | \\   | # Double and single backslash, with escaping
          \|   | \|\|   # Pipe and double pipe, with escaping
        )\b
        ''', re.X)

    def lookup(self, color: str) -> str:
        if color.startswith('!'):
            name = color[1:]
            if name not in mcolors.CSS4_COLORS:
                raise ValueError(f"Unknown named color {name}")
            return name
        elif color.startswith('#') and len(color) == 7: # RGB as-is
            return color

        return self.colors.get(color, '#FF00FF')

    def paint(self, colorspec: str) -> dict[str, Any]:
        # colorspec is built from a stripe's org field
        # which contains one of:
        # 1. a single org 'mzw'
        # 2. a named color starting with a bang
        # 3. a hex color starting with a hash
        # 4. two colors joined with matplotlib's hatch char
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

