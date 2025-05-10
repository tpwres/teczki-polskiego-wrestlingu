import sys
from pathlib import Path
srcdir = Path(__file__).resolve().parent / '..'
sys.path.insert(0, str(srcdir))
import argparse
from sys import stdin, stdout
from types import SimpleNamespace
from dateutil.rrule import YEARLY, MONTHLY
from datetime import datetime, timedelta
import matplotlib as mpl
from matplotlib import pyplot as plt
from matplotlib import patches as pat
from matplotlib import colors
from matplotlib import transforms
from matplotlib.dates import AutoDateLocator
from utils import SkipComments
import csv
from itertools import groupby
import tomllib
from collections import defaultdict
import math

def setup():
    pass

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

class CareerRow:
    def __init__(self, row):
        name, org, start, end = row
        self.name = name
        self.org = org
        self.start = ym(start)
        self.end = ym(end)
        if end == '-':
            self.duration = datetime.today() - self.start
        else:
            self.duration = self.end - self.start

    def overlaps(self, other_row):
        if self.start >= other_row.end:
            return False
        if self.end <= other_row.start:
            return False
        return True

    def __repr__(self):
        return f"({self.name}@{self.org},start={self.start},end={self.end},dur={self.duration})"

def process(in_fd, out_fd):
    io = SkipComments(in_fd)
    data = list(CareerRow(row) for row in csv.reader(io))

    # Data is formatted like this
    # name,org,start-date,end-date
    # For each name, produce a list of line segments, each starting at start-date, ending at end-date
    # and with the color looked up by org in an org_colors map
    colors = load_org_colors()
    fallback_color = '#000'

    _fig, ax = plt.subplots(figsize=(10, 6),layout='constrained')
    loc = AutoDateLocator()
    loc.intervald[YEARLY] = [1]
    ax.xaxis.set_major_locator(loc)
    loc = AutoDateLocator()
    loc.intervald[MONTHLY] = [3]
    ax.xaxis.set_minor_locator(loc)
    ax.xaxis.grid(visible=True, alpha=0.4)


    # Grab all intervals, sort by length descending
    # Pick the first, longest one, place it on the first row. Remember the row for its org.
    # Take the next one. If it overlaps in any items in the first row, put it on the next row and remember row.
    # But if it doesn't overlap, add it to the first row and remember.
    labels = {}
    grouped_by_name = groupby(data, lambda row: row.name)
    rownum = 0
    for name, rows in grouped_by_name:
        sys.stderr.write(name + "\n")
        labels[rownum] = name
        # rows = sorted(list(rows), key=lambda row: row.duration, reverse=True)
        rows = list(rows)
        row_contents = defaultdict(list)
        while rows:
            longest = rows.pop(0)
            which_row = None
            # Find a row this can fit in
            # Start with most packed row first, then go through less packed
            for maybe_rownum, content in sorted(row_contents.items(), key=lambda rc: len(rc[1]), reverse=True):
                if any(r.overlaps(longest) for r in content):
                    continue
                else: # No overlap in this row
                    which_row = maybe_rownum
            if which_row is None:
                # Didn't find a place
                which_row = max(row_contents.keys()) + 1 if row_contents else rownum
            row_contents[which_row].append(longest)

        # At this point:
        # rows has been consumed
        # row_contents maps row numbers to lists of bars that fit there, longest first
        # IDEA: Those aren't consecutive rows. Those are LAYERS
        draw_rows = list(row_contents.items())
        max_row = max(r for r, _bars in draw_rows)
        frac_step = 1.0

        for rowindex, bars in draw_rows:
            sys.stderr.write(f"{rowindex} {bars}\n")
            offset = rowindex - rownum
            for bar in bars:
                ax.barh(rownum + offset * frac_step, bar.duration, left=bar.start, color=colors.get(bar.org, fallback_color), height=1.0)
        rownum = rownum + math.ceil(frac_step * len(draw_rows)) + 1

    y_pos = list(labels.keys())
    ax.set_yticks(y_pos, [labels[i] for i in y_pos])
    ax.invert_yaxis()

    # Create legend by adding patches
    legend_artists = [pat.Rectangle((0, 0), 0.5, 0.5, color=color) for _key, color in colors.items()]
    legend_keys = colors.keys()
    _fig.legend(legend_artists, legend_keys,loc='outside right lower')


    ax.set_xlim(left=None, right=datetime.now())
    # Important dates for The Greens
    ax.vlines(ymd('2021-10-27'), 0, 1, transform=ax.get_xaxis_transform()) # Green Revolution
    ax.vlines(ymd('2024-06-05'), 0, 1, transform=ax.get_xaxis_transform()) # Post-TBFTP Exits
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
