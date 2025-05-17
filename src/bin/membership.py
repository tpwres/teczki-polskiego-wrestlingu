import sys
from pathlib import Path
srcdir = Path(__file__).resolve().parent / '..'
sys.path.insert(0, str(srcdir))
from io import BytesIO
import argparse
from sys import stdin, stdout
from types import SimpleNamespace
from typing import Tuple
from datetime import datetime
import matplotlib as mpl
from matplotlib import pyplot as plt, text as mtxt
from matplotlib.dates import YearLocator, MonthLocator
from utils import SkipComments
import csv
from timelines import Stripe, OrgColors, Annotator, LegendBuilder, SVGFilter, Directive
from page import page

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

    yield (current_name, batch)

def make_org_entry(org_identifier):
    content_root = Path("content")
    org_path = f"o/{org_identifier}.md"
    org_page = page(content_root / org_path)
    return f"[o/{org_page.title}]"

class Grapher:
    def __init__(self):
        self.setup_matplotlib()
        self.colors = OrgColors()
        self.annotator = Annotator()
        self.legend_builder = LegendBuilder(self.colors, make_org_entry)

    def setup_matplotlib(self):
        plt.rcParams["hatch.linewidth"] = 6
        # Otherwise text is converted to svg paths
        mpl.rcParams["svg.fonttype"] = 'none'

    def load_csv(self, io) -> Tuple[list[Stripe], list[Directive]]:
        stripes, directives = [], []
        for row in csv.reader(io):
            if Directive.matches(row):
                directives.append(Directive(row))
            else:
                stripes.append(Stripe(row))

        return (stripes, directives)

    def process(self, in_fd, out_fd):
        io = SkipComments(in_fd)
        data, instructions = self.load_csv(io)

        _fig, ax = plt.subplots(figsize=(10, 5), layout='constrained')
        ax.xaxis.set_major_locator(YearLocator())
        ax.xaxis.set_minor_locator(MonthLocator(bymonth=[4,7,10]))
        ax.xaxis.grid(visible=True, alpha=0.4, which='both')

        self.process_directives(instructions, ax)
        labels = self.draw_stripes(data, ax)
        legend_keys, patches = self.legend_builder.legend()
        _fig.legend(patches, legend_keys, loc='outside lower right', facecolor='#ff00ff')

        y_pos = list(labels.keys())
        ax.set_yticks(y_pos, [labels[i] for i in y_pos])
        ax.invert_yaxis()

        # Set colors to placeholders
        ax.spines['left'].set_color('#ff00ff')
        ax.spines['left'].set_gid('left-spine')
        ax.spines['top'].set_color('#ff00ff')
        ax.spines['top'].set_gid('top-spine')
        ax.spines['bottom'].set_color('#ff00ff')
        ax.spines['bottom'].set_gid('bottom-spine')
        ax.spines['right'].set_color('#ff00ff')
        ax.spines['right'].set_gid('right-spine')
        ax.tick_params(axis='x', colors='#ff00ff')
        ax.tick_params(axis='y', colors='#ff00ff')

        # The graph ends at today
        ax.set_xlim(left=None, right=datetime.now())
        # Write out the SVG
        plt.savefig(out_fd, format='svg', pad_inches=0, transparent=True)

    def process_directives(self, directives: list[Directive], ax):
        for i, directive in enumerate(directives):
            match directive:
                case Directive(keyword='@color', params=[str(symbol), str(colorspec)]):
                    self.colors.add_custom(symbol, colorspec)
                case Directive(keyword='@vline', params=[date, colorspec, text]):
                    # TODO: restore ym/ymd behavior?
                    left = datetime.strptime(date, '%Y-%m-%d')
                    self.add_vline(ax, left, text, colorspec, i)
                case Directive(keyword='@legend', params=[str(symbol), str(text)]):
                    self.legend_builder.add_explicit(symbol, text)


    def draw_stripes(self, data, ax) -> dict[str, str]:
        labels = {}
        rownum = 0
        for name, stripes in group_rows_by_name(data):
            stripes = list(stripes)
            # Rows for the same name are listed as consecutive groups
            for layer_index, (_, layer_stripes) in enumerate(layers(stripes)):
                for stripe_index, stripe in enumerate(layer_stripes):
                    labels[rownum] = name
                    self.legend_builder.add_stripe(stripe)
                    self.add_bars(ax, rownum + layer_index, stripe, stripe_index)
                    #self.annotator.annotate(ax, rownum + layer_index, stripe, stripe_index)

            rownum += layer_index + 1 # pyright: ignore

        return labels

    def add_vline(self, ax, left: datetime, text: str, colorspec: str, index):
        t = ax.get_xaxis_transform()
        ax.vlines(
            left,
            0, 1, transform=t, # Spans the whole graph height
            **self.colors.line(colorspec)
        )
        ax.text(
            left,
            0.05,
            text,
            rotation='vertical',
            transform=t,
            gid=f"vline-text-{index}",
            color='#ff00ff',
            bbox=dict(facecolor='#ff00fe', edgecolor='#ff00ff', alpha=0.5)
        )

    def add_bars(self, ax, rownum, stripe, index):
        full_height = 0.8
        for n, d in stripe.band:
            match (n, d):
                case (1, 1):
                    stripe_height, stripe_offset = full_height, 0
                case (n, d):
                    stripe_height = full_height / d
                    top = -full_height / 2 + stripe_height / 2
                    stripe_offset = top + (n-1) * stripe_height

            ax.barh(rownum - stripe_offset,
                    stripe.duration,
                    left=stripe.start,
                    height=stripe_height,
                    gid=f"stripe-{rownum}-{index}-{n}-{d}",
                    **self.colors.paint(stripe.org)
            )


def main():
    options = parse_args()
    grapher = Grapher()
    grapher.process(options.input_file, raw_svg := BytesIO())
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
