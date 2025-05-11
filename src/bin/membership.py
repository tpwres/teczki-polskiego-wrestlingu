import sys
from pathlib import Path
srcdir = Path(__file__).resolve().parent / '..'
sys.path.insert(0, str(srcdir))
import re
import argparse
from typing import ClassVar, Any
from sys import stdin, stdout
from types import SimpleNamespace
from dateutil.rrule import YEARLY, MONTHLY
from datetime import datetime, timedelta
import matplotlib as mpl
from matplotlib import pyplot as plt
from matplotlib import patches as pat
from matplotlib import colors
from matplotlib import transforms
from matplotlib.dates import AutoDateLocator, YearLocator, MonthLocator
from utils import SkipComments
import csv
from itertools import groupby
import tomllib
from collections import defaultdict
import math

def setup():
    Stripe.org_colors = load_org_colors()
    plt.rcParams["hatch.linewidth"] = 6

def load_org_colors():
    config_path = Path(__file__).parent / '../..' / 'config.toml'
    with config_path.resolve().open('rb') as fp:
        project_config = tomllib.load(fp)
        styles = project_config['extra']['org_styles']
        return {key: org['bg'] for key, org in styles.items()}

def ym(text: str) -> datetime:
    "Parses year-month date into a datetime object."
    return datetime.strptime('2099-12' if text == '-' else text, '%Y-%m')

def ymd(text: str) -> datetime:
    return datetime.strptime('2099-12-31' if text == '-' else text, '%Y-%m-%d')

class Stripe:
    org_colors: ClassVar[dict[str, str]]
    fallback_color: ClassVar[str] = '#000'

    def __init__(self, row):
        name, org, start, end, *rest = row
        self.name, self.org = name, org
        self.start = ymd(start) if start.count('-') == 2 else ym(start)
        self.end = ymd(end) if end.count('-') == 2 else ym(end)
        if end == '-':
            self.duration = datetime.today() - self.start
        else:
            self.duration = self.end - self.start
        match rest:
            case [layer, band]:
                self.layer = layer
                self.band = tuple(int(num) for num in band.split('/'))
            case [layer]:
                self.layer = layer
                self.band = (1, 1)
            case []:
                self.layer = '0'
                self.band = (1, 1)


    def overlaps(self, other_row):
        if self.start >= other_row.end:
            return False
        if self.end <= other_row.start:
            return False
        return True

    def render_args(self) -> dict[str, Any]:
        return self.rich_colors() or dict(
            color=Stripe.single_color(self.org)
        )

    @staticmethod
    def single_color(org):
        return Stripe.org_colors.get(org, Stripe.fallback_color)

    @property
    def all_orgs(self):
        match re.match(r'^(\w+)([|/\\])(\w+)$', self.org):
            case re.Match(group=group):
                return set([group(1), group(3)])
            case _:
                return set([self.org])

    def rich_colors(self):
        match re.match(r'^(\w+)([|/\\])(\w+)$', self.org):
            case re.Match(group=group):
                return dict(
                    facecolor=Stripe.single_color(group(1)),
                    edgecolor=Stripe.single_color(group(3)),
                    hatch=group(2),

                )
            case _:
                return None

    def __repr__(self):
        return f"({self.name}@{self.org},{self.start}..{self.end},dur={self.duration},layer={self.layer},band={self.band})"

def layers(stripes: list[Stripe]):
    # Group the list of stripes by layers, and yield them in-order
    # Ordering is ASCII-lexical, i.e. A before B before C etc.
    all_layers = sorted(set(stripe.layer for stripe in stripes))
    for layer in all_layers:
        yield (layer, (stripe for stripe in stripes if stripe.layer == layer))

def log(message):
    sys.stderr.write(message + "\n")

def process(in_fd, out_fd):
    io = SkipComments(in_fd)
    data = list(Stripe(row) for row in csv.reader(io))

    # For each name, produce a list of line segments, each starting at start-date, ending at end-date
    # and with the color looked up by org in an org_colors map

    _fig, ax = plt.subplots(figsize=(10, 4),layout='constrained')
    ax.xaxis.set_major_locator(YearLocator())
    ax.xaxis.set_minor_locator(MonthLocator(bymonth=[4,7,10]))
    ax.xaxis.grid(visible=True, alpha=0.4, which='both')

    labels = {}
    orgs_used = set()
    rownum = 0
    full_height = 0.8
    for name, stripes in groupby(data, lambda row: row.name):
        stripes = list(stripes)
        # Rows for the same name are listed as consecutive groups
        for layer_index, (ls, layer_stripes) in enumerate(layers(stripes)):
            for stripe in layer_stripes:
                if ls == '!':
                    ax.vlines(stripe.start, 0, 1, transform=ax.get_xaxis_transform())
                    ax.text(stripe.start, 0, stripe.name, rotation='vertical', transform=ax.get_xaxis_transform())
                    continue
                labels[rownum] = name
                orgs_used |= stripe.all_orgs
                match stripe.band:
                    case (1, 1):
                        stripe_height = full_height
                        stripe_offset = 0
                    case (n, d):
                        stripe_height = full_height / d
                        top = -full_height / 2 + stripe_height / 2
                        stripe_offset = top + (n-1) * stripe_height

                ax.barh(rownum + layer_index - stripe_offset,
                        stripe.duration,
                        left=stripe.start,
                        height=stripe_height,
                        **stripe.render_args()
                )
        rownum += layer_index + 1

    # Create legend by adding patches
    log(f"OU = {orgs_used}")
    legend_artists = [pat.Rectangle((0, 0), 0.5, 0.5, color=Stripe.single_color(org)) for org in orgs_used]
    legend_keys = list(orgs_used)
    _fig.legend(legend_artists, legend_keys,loc='outside right lower')

    y_pos = list(labels.keys())
    ax.set_yticks(y_pos, [labels[i] for i in y_pos])
    ax.invert_yaxis()

    ax.set_xlim(left=None, right=datetime.now())
    # plt.tight_layout()
    plt.savefig(out_fd, format='svg', pad_inches=0, transparent=True)


def main():
    setup()
    options = parse_args()
    process(options.input_file, options.output_file)

def parse_args():
  parser = argparse.ArgumentParser(description="Process some input")
  parser.add_argument("input", help="Input file (optional)", default='-', nargs='?')
  parser.add_argument("output", help="Output file (optional)", default='-', nargs='?')
  args = parser.parse_args()

  input_file = stdin if args.input == '-' else Path(args.input).open('r')
  output_file = stdout if args.output == '-' else Path(args.output).open('w')

  return SimpleNamespace(input_file=input_file, output_file=output_file)

if __name__ == "__main__":
    main()
