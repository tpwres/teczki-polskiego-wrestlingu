import sys
from pathlib import Path
srcdir = Path(__file__).resolve().parent / '..'
sys.path.insert(0, str(srcdir))
from io import BytesIO
import argparse
from sys import stdin, stdout
from types import SimpleNamespace
from dateutil.rrule import YEARLY, MONTHLY
from datetime import datetime
import matplotlib as mpl
from matplotlib import pyplot as plt
from matplotlib import patches as pat
from matplotlib.dates import AutoDateLocator, YearLocator, MonthLocator
from utils import SkipComments
import csv
from timelines import Stripe, OrgColors, Annotator, LegendBuilder, SVGFilter

def setup():
    plt.rcParams["hatch.linewidth"] = 6
    # Otherwise text is converted to svg paths
    mpl.rcParams["svg.fonttype"] = 'none'

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

def group_rows_by_name(stripes):
    current_name = None
    batch = []
    for stripe in stripes:
        if stripe.name == current_name:
            batch.append(stripe)
        elif stripe.name == '-' and current_name:
            batch.append(stripe)
        else:
            if current_name:
                yield(current_name, batch)
            batch = []
            current_name = stripe.name
            batch.append(stripe)

def add_vertical_line_and_text(ax, stripe, colors):
    t = ax.get_xaxis_transform()
    ax.vlines(
        stripe.start,
        0, 1, transform=t, # Spans the whole graph height
        **colors.line(stripe.org)
    )
    ax.text(
        stripe.start,
        0,
        stripe.name,
        rotation='vertical',
        transform=t
    )

def add_bars(ax, row, stripe, colors, index):
    full_height = 0.8
    for n, d in stripe.band:
        match (n, d):
            case (1, 1):
                stripe_height = full_height
                stripe_offset = 0
            case (n, d):
                stripe_height = full_height / d
                top = -full_height / 2 + stripe_height / 2
                stripe_offset = top + (n-1) * stripe_height

        ax.barh(row - stripe_offset,
                stripe.duration,
                left=stripe.start,
                height=stripe_height,
                gid=f"stripe-{row}-{index}-{n}-{d}",
                **colors.paint(stripe.org)
        )
def process(in_fd, out_fd):
    io = SkipComments(in_fd)
    data = list(Stripe(row) for row in csv.reader(io))
    colors = OrgColors()
    annotator = Annotator()
    legend_builder = LegendBuilder(colors, make_org_entry)

    # For each name, produce a list of line segments, each starting at start-date, ending at end-date
    # and with the color looked up by org in an org_colors map

    _fig, ax = plt.subplots(figsize=(10, 4),layout='constrained')
    ax.xaxis.set_major_locator(YearLocator())
    ax.xaxis.set_minor_locator(MonthLocator(bymonth=[4,7,10]))
    ax.xaxis.grid(visible=True, alpha=0.4, which='both')

    labels = {}
    rownum = 0
    for name, stripes in group_rows_by_name(data):
        stripes = list(stripes)
        # Rows for the same name are listed as consecutive groups
        for layer_index, (ls, layer_stripes) in enumerate(layers(stripes)):
            for stripe_index, stripe in enumerate(layer_stripes):
                if ls == '!':
                    add_vertical_line_and_text(ax, stripe, colors)
                    continue

                labels[rownum] = name
                legend_builder.add_stripe(stripe)
                add_bars(ax, rownum + layer_index, stripe, colors, stripe_index)
                #annotator.annotate(ax, rownum + layer_index, stripe, stripe_index)

        rownum += layer_index + 1

    # TODO: build the org list
    #legend_artists = [pat.Rectangle((0, 0), 0.5, 0.5, color=Stripe.single_color(org)) for org in orgs_used]
    #legend_keys = list(orgs_used)
    legend_keys, patches = legend_builder.legend()
    _fig.legend(patches, legend_keys ,loc='outside lower right', facecolor='#ff00ff')

    y_pos = list(labels.keys())
    ax.set_yticks(y_pos, [labels[i] for i in y_pos])
    ax.invert_yaxis()

    ax.set_xlim(left=None, right=datetime.now())
    # plt.tight_layout()
    plt.savefig(out_fd, format='svg', pad_inches=0, transparent=True)


def main():
    setup()
    options = parse_args()
    process(options.input_file, raw_svg := BytesIO())
    raw_svg.seek(0)
    filter = SVGFilter()
    filter.process(raw_svg, options.output_file)

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
