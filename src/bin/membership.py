import sys
from pathlib import Path
srcdir = Path(__file__).resolve().parent / '..'
sys.path.insert(0, str(srcdir))
import argparse
from sys import stdin, stdout
from types import SimpleNamespace
from dateutil.rrule import YEARLY, MONTHLY
from datetime import datetime
import matplotlib as mpl
from matplotlib import pyplot as plt
from matplotlib import patches as pat
from matplotlib import colors
from matplotlib import transforms
from matplotlib.dates import AutoDateLocator, YearLocator, MonthLocator
from utils import SkipComments
import csv
from itertools import groupby
from timelines import Stripe, OrgColors

def setup():
    plt.rcParams["hatch.linewidth"] = 6

def ym(text: str) -> datetime:
    "Parses year-month date into a datetime object."
    return datetime.strptime('2099-12' if text == '-' else text, '%Y-%m')

def ymd(text: str) -> datetime:
    return datetime.strptime('2099-12-31' if text == '-' else text, '%Y-%m-%d')


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
    colors = OrgColors()

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
                    ax.vlines(stripe.start, 0, 1, transform=ax.get_xaxis_transform(), **colors.paint(stripe.org))
                    ax.text(stripe.start, 0, stripe.name, rotation='vertical', transform=ax.get_xaxis_transform())
                    continue

                labels[rownum] = name
                orgs_used |= stripe.all_orgs
                for n, d in stripe.band:
                    match (n, d):
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
                            **colors.paint(stripe.org)
                    )
        rownum += layer_index + 1

    # Create legend by adding patches
    log(f"OU = {orgs_used}")
    # TODO: build the org list
    #legend_artists = [pat.Rectangle((0, 0), 0.5, 0.5, color=Stripe.single_color(org)) for org in orgs_used]
    #legend_keys = list(orgs_used)
    #_fig.legend(legend_artists, legend_keys,loc='outside right lower')

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
