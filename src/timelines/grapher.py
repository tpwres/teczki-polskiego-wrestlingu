import csv
from dataclasses import dataclass
from datetime import datetime, date
from pathlib import Path
import sys
from typing import Tuple, Any
import matplotlib as mpl
from matplotlib import pyplot as plt, patches as pat, transforms
from matplotlib.dates import YearLocator, MonthLocator
import numpy as np

from page import page
from utils import SkipComments

from .directive import Directive
from .stripe import Stripe
from .org_colors import OrgColors
from .annotator import Annotator
from .legend_builder import LegendBuilder

@dataclass
class ArrowAnnotation:
    start: date
    row_a: int
    end: date
    row_b: int

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
        self.extra_metadata = {}
        self.arrow_annotations = []
        self.options: dict[str, Any] = {
            'bar_height': 0.8,
            'figsize': '10/5',
            'hide_spines': '',
            'layout': 'constrained',
            'legend': 'on',
            'major_ticks': '1y',
            'minor_ticks': 'off',
            'org_in_tooltip': 'on',
            'padding': 0.4,
            'rotate_xticks': 'off',
        }

    @property
    def bar_height(self) -> float:
        return float(self.options['bar_height'])

    @property
    def rotate_ticks(self) -> bool:
        return self.options['rotate_xticks'] == 'on'

    @property
    def display_legend(self) -> bool:
        return self.options['legend'] == 'on'

    @property
    def quarterly_minor_ticks(self) -> bool:
        return self.options['minor_ticks'] == '3m'

    @property
    def layout(self) -> str:
        return self.options['layout']

    @property
    def figsize(self) -> Tuple[float, float]:
        opt = self.options['figsize']
        w, h = [float(v) for v in opt.split('/')]
        return (w, h)

    @property
    def visible_spines(self) -> set[str]:
        visible = {'top', 'left', 'bottom', 'right'}
        for spine in self.options['hide_spines'].split('+'):
            visible -= {spine}
        return visible

    @property
    def major_tick_years(self):
        opt = self.options['major_ticks']
        if opt == '1y':
            return 1
        elif opt == '2y':
            return 2
        raise ValueError(f"Unsupported major_ticks value {opt}")

    @property
    def org_in_tooltip(self) -> bool:
        return self.options['org_in_tooltip'] == 'on'

    @property
    def padding(self) -> float:
        return float(self.options['padding'])

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

        self.process_directives(instructions, None)

        _fig, ax = plt.subplots(figsize=self.figsize, layout=self.layout)
        self.process_directives(instructions, ax)

        ax.xaxis.set_major_locator(YearLocator(self.major_tick_years))
        if self.quarterly_minor_ticks:
            ax.xaxis.set_minor_locator(MonthLocator(bymonth=[4,7,10]))
        ax.xaxis.grid(visible=True, alpha=0.4, which='both')

        labels = self.draw_stripes(data, ax)
        self.add_bg_stripes(ax, len(labels))
        self.add_arrows(_fig, ax)

        if self.display_legend:
            legend_keys, patches = self.legend_builder.legend()
            _fig.legend(patches, legend_keys, loc='outside lower right', facecolor='#ff00ff')
        else:
            _fig.legends = []

        if self.rotate_ticks:
            ax.xaxis.set_tick_params(rotation=90)

        y_pos = list(labels.keys())
        ax.set_yticks(y_pos, [labels[i] for i in y_pos])
        h2_pad = self.bar_height / 2 + self.padding
        ax.set_ylim(0 - h2_pad, len(labels) - 1 + h2_pad)
        ax.invert_yaxis()

        self.set_placeholder_colors(ax)

        # The graph ends at today
        ax.set_xlim(left=None, right=datetime.now())
        # Write out the SVG
        plt.savefig(out_fd, format='svg', pad_inches=0, transparent=True)

    def process_directives(self, directives: list[Directive], ax):
        for i, directive in enumerate(directives):
            self.handle_directive(directive, ax, i)

    def handle_directive(self, directive, ax, index):
        match directive:
            case Directive(keyword='@color', params=[str(symbol), str(colorspec)]):
                self.colors.add_custom(symbol, colorspec)
            case Directive(keyword='@vline', params=[date, colorspec, text, target]) if ax:
                # TODO: restore ym/ymd behavior?
                left = datetime.strptime(date, '%Y-%m-%d')
                gid = self.add_vline(ax, left, text, colorspec, index)
                self.extra_metadata[gid] = {'href': target}
            case Directive(keyword='@vline', params=[date, colorspec, text]) if ax:
                left = datetime.strptime(date, '%Y-%m-%d')
                self.add_vline(ax, left, text, colorspec, index)
            case Directive(keyword='@legend', params=[str(symbol), str(text), str(target)]):
                self.legend_builder.add_explicit(symbol, text)
                self.add_explicit_link(text, target)
            case Directive(keyword='@legend', params=[str(symbol), str(text)]):
                self.legend_builder.add_explicit(symbol, text)
            case Directive(keyword='@link', params=[str(key), str(target)]):
                self.add_explicit_link(key, target)
            case Directive(keyword='@option', params=[str(key), str(value)]):
                self.options[key] = value
            case Directive(keyword='@arrow', params=[str(start), str(row_a), str(end), str(row_b)]):
                start = datetime.strptime(start, '%Y-%m')
                end = datetime.strptime(end, '%Y-%m')
                row_a, row_b = int(row_a), int(row_b)
                self.arrow_annotations.append(ArrowAnnotation(start, row_a, end, row_b))

    def draw_stripes(self, data, ax) -> dict[str, str]:
        labels = {}
        rownum = 0
        for name, stripes in group_rows_by_name(data):
            stripes = list(stripes)
            # Rows for the same name are listed as consecutive groups
            for layer_index, (_, layer_stripes) in enumerate(layers(stripes)):
                for stripe_index, stripe in enumerate(layer_stripes):
                    labels[rownum] = name
                    self.add_stripe_to_legend(stripe)
                    self.add_bars(ax, rownum + layer_index, stripe, stripe_index)

            rownum += layer_index + 1 # pyright: ignore

        return labels

    def add_vline(self, ax, left: datetime, text: str, colorspec: str, index) -> str:
        t = ax.get_xaxis_transform()
        ax.vlines(
            left,
            0, 1, transform=t, # Spans the whole graph height
            gid=f"vline-{index}",
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
            bbox=self.text_bbox(text)
        )
        return f"vline-text-{index}"

    def text_bbox(self, text: str, ):
        return dict(facecolor='#ff00fe', edgecolor='none', alpha=0.7, pad=2)

    def add_bars(self, ax, rownum, stripe, index):
        full_height = self.bar_height
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
            self.annotate(ax, stripe, top=rownum-stripe_offset, identifier=f"ann-{rownum}-{index}-{n}-{d}")

    def annotate(self, ax, stripe, top, identifier):
        self.annotator.annotate(ax, stripe, top, identifier, self.org_in_tooltip)

    def add_stripe_to_legend(self, stripe: Stripe):
        if self.display_legend:
            self.legend_builder.add_stripe(stripe)

    def add_bg_stripes(self, ax, numrows):
        fig = ax.figure
        tx = transforms.blended_transform_factory(ax.transAxes, ax.transData)

        for i in range(numrows):
            rr = pat.Rectangle(
                xy=(-1, i - self.bar_height / 2),
                width=2.2, height=self.bar_height,
                color='#ff00ff', edgecolor=None,
                transform=tx, gid=f"bg-{i}"
            )
            rr.set_zorder(-1)
            fig.add_artist(rr)

    def add_arrows(self, fig, ax):
        for arrow in self.arrow_annotations:
            startx, starty = arrow.start, arrow.row_a - 1
            endx, endy = arrow.end, arrow.row_b - 1
            midx = startx + (endx - startx) / 2
            # Segments
            ax.annotate(
                "",
                xy=(midx,starty),
                xytext=(startx, starty),
                arrowprops=dict(facecolor='black', width=0.2, headwidth=0)
            )
            ax.annotate(
                "",
                xy=(midx,endy),
                xytext=(midx,starty),
                arrowprops=dict(facecolor='black', width=0.2, headwidth=0)
            )
            ax.annotate(
                "",
                xy=(endx, endy),
                xytext=(midx,endy),
                arrowprops=dict(facecolor='black', width=0.2, headwidth=4.0, headlength=2.0)
            )

    def add_explicit_link(self, key, target):
        links = self.extra_metadata.setdefault('links', {})
        links[key] = {'href': target}

    def set_placeholder_colors(self, ax):
        # Set colors to placeholders
        # TODO: now the method name is wrong
        for position in ('left', 'top', 'bottom', 'right'):
            if position in self.visible_spines:
                ax.spines[position].set_color('#ff00ff')
                ax.spines[position].set_gid(f'{position}-spine')
            else:
                ax.spines[position].set_visible(False)

        ax.tick_params(axis='x', colors='#ff00ff')
        ax.tick_params(axis='y', colors='#ff00ff')
