#! /usr/bin/env python3

from pathlib import Path
from dateutil.rrule import YEARLY
from matplotlib import pyplot as plt
import matplotlib as mpl
from matplotlib import colors
from matplotlib.dates import AutoDateLocator
from sys import argv, stdout
from datetime import datetime, timedelta
import csv
from typing import TextIO

class SkipComments:
    """
    Wraps an IO object, and provides iteration over its lines.
    Skips lines that start with a comment marker (#)
    """
    def __init__(self, io: TextIO):
        self.io = iter(io.readlines())

    def __iter__(self):
        return self

    def __next__(self) -> str:
        while True:
            line = next(self.io)
            if not line.startswith('#'):
                break

        return line

def ym(text: str) -> datetime:
    "Parses year-month date into a datetime object."
    return datetime.strptime(text, '%Y-%m')

def main(source_filename: Path, output_stream: TextIO):
    io = SkipComments(source_filename.open())
    data = list(csv.reader(io))

    _fig, ax = plt.subplots(figsize=(10, 6))

    # Axis setup
    ax.set_xlim(left=ym('1990-01'), right=datetime.now())
    # Set major ticks at 4 years, minor at 2
    loc = AutoDateLocator()
    loc.intervald[YEARLY] = [2]
    ax.xaxis.set_major_locator(loc)
    loc = AutoDateLocator()
    loc.intervald[YEARLY] = [1]
    ax.xaxis.set_minor_locator(loc)

    # Select palette. Replicate the one that gnuplot generated.
    colormap = build_colormap()

    # Labels are assigned after we draw all bars
    labels = []

    for index, title, low, high, color_index in data:
        index = int(index)
        low, high = ym(low), ym(high)
        d: timedelta = high - low

        if title and title not in labels:
            labels.append(title)

        c = int(color_index)
        # Note that low is a datetime object, and d (width) is a timedelta value
        ax.barh(index, d, left=low, color=colormap(c))

    # Assign tick labels on the y axis. Range starts from 1 to match csv file
    y_pos = [x for x in range(1, len(labels)+1)]
    ax.set_yticks(y_pos, labels=labels)
    ax.set_ylim(top=1-0.8, bottom=len(labels)+0.8) # 0.8 is the bar thickness

    ax.spines['right'].set_visible(False)
    ax.spines['top'].set_visible(False)

    plt.xticks(rotation=90)

    # Otherwise ytick labels are clipped
    plt.tight_layout()
    # bbox_inches and pad_inches control padding
    plt.savefig(output_stream, format='svg', pad_inches=0, transparent=True)
    # plt.show()

def build_colormap():
    return colors.ListedColormap([
        'gray',
        '#9400d3',
        '#009e73',
        '#56b4e9',
        '#e69f00',
        '#f0e442',
        '#0072b2',
        '#e51e10',
        '#10e5c9'
    ])

def setup():
    # Otherwise text is converted to svg paths
    mpl.rcParams['svg.fonttype'] = 'none'

if __name__ == "__main__":
    setup()
    main(Path(argv[1]), stdout)
