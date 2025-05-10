#! /usr/bin/env python3

from pathlib import Path
from dateutil.rrule import YEARLY
import matplotlib as mpl
from matplotlib import pyplot as plt
from matplotlib import patches as pat
from matplotlib import colors
from matplotlib import transforms
from matplotlib.dates import AutoDateLocator
from sys import argv, stdout, stderr
from datetime import datetime, timedelta
import csv
from typing import TextIO
from utils import SkipComments

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
    ax.xaxis.grid(visible=True, alpha=0.4)

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
        ax.barh(index, d, left=low, color=colormap(c), gid=f"bar-{index}-{color_index}")
        ax.annotate(annotation_text(low, high),
                    xy=(low, index),
                    xytext=(-5, 1.5), textcoords='offset fontsize',
                    # This facecolor is later replaced
                    bbox=dict(boxstyle='square', facecolor='#ff00ff'),
                    gid=f"ann-{index}-{color_index}",
                    annotation_clip=False)

    # Assign tick labels on the y axis. Range starts from 1 to match csv file
    y_pos = [x for x in range(1, len(labels)+1)]
    ax.set_yticks(y_pos, labels=labels)
    # Invert yaxis: normally 0 is at the bottom, N at the top
    ax.invert_yaxis()

    # X coordinate is in axes (0 is Y axis, 1 is right end of graph)
    # and Y coord is in data (from 0 to N)
    tx = transforms.blended_transform_factory(ax.transAxes, ax.transData)
    for i in range(1, len(labels)+1):
        # Start rectangle at -1 to span left of the Y axis. Width is more than the entire graph's worth.
        rr = pat.Rectangle(xy=(-1, i-0.5), width=2.2, height=1,
                           color='#f0f', edgecolor=None, transform=tx, gid=f"bg-{i}")
        # Emitted in SVG before the figure
        rr.set_zorder(-1)
        _fig.add_artist(rr)

    ax.spines['right'].set_visible(False)
    ax.spines['top'].set_visible(False)

    plt.xticks(rotation=90)

    # Otherwise ytick labels are clipped
    plt.tight_layout()
    # bbox_inches and pad_inches control padding
    plt.savefig(output_stream, format='svg', pad_inches=0, transparent=True)

def annotation_text(low, high):
    if high.year == 2099:
        return f"since {low.strftime('%b %Y')}"
    else:
        return f"{low.strftime('%b %Y')} - {high.strftime('%b %Y')}"

def build_colormap():
    return colors.ListedColormap([
        'gray', #backyard
        '#FFFF00', #SupronStars
        '#BFCCFF', #PPWF
        '#FF9E23', #DDW
        '#FF0000', #TBW
        '#770077', #PpW
        '#00B200', #MZW
        '#0066CC', #KPW
        '#000000', #PTW
        '#B24C4C'  #LOW
    ])

def setup():
    # Otherwise text is converted to svg paths
    mpl.rcParams['svg.fonttype'] = 'none'

if __name__ == "__main__":
    setup()
    main(Path(argv[1]), stdout)
