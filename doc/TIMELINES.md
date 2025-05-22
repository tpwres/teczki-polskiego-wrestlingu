# Timelines

Timelines are graphs presenting events or changes through time. The X axis is always time, and the Y axis is usually categorical, representing some entity rather than process. A concrete example is talent moving across promotions, where different colored bars could represent their time spent in one.

A timeline is usually defined with a CSV file, though some timelines may be generated automatically from the events database.

## CSV

The most important kind of row is the stripe, defined by start and end date. For example, here's an incomplete career of a famous wrestler, with dates sourced from Cagematch:

```csv
Chris Jericho,cnwa,1991-02-01,1991-04-12
-,fmw,1991-10-10,1991-10-24
-,ecw,1996-02-02,1996-08-03
-,wcw,1996-08-20,1999-07-21
-,njpw,1997-01-04,1998-09-23
-,wwf,1999-08-21,2001-12-21
-,wwe,2001-12-21,2018-04-27
-,njpw,2018-01-04,-
-,aew,2019,05-25,-
```

The four required fields are: `name, orgs, start, end`. Some fields use a single dash `-` for special purposes.

* a dash in the name field associates this row with the previous name
* in the end column, it means "until now"

## Colors

The `org` field specifies the color. It can be either of:

1. a single organization symbol. A configured brand color is be used if found, otherwise the primary color (depending on light/dark mode) is used.
2. a named color, prefixed with a single bang `!`. Only names from the [CSS 4 Named Colors](https://www.w3.org/TR/css-color-4/#named-colors) are supported.
3. a hex color specification, e.g. #dc143c for crimson
4. two of the above (org, named or hex colors) joined with a _hatch symbol_

Single colors or org names (1, 2, 3) give the bar a solid appearance. When using two colors, a hatch symbol defines how they are rendered together.

* a pipe `|` or doubled pipe `||` produces vertical stripes
* a slash `/` or doubled slash `//` draws stripes slanted to the right
* a backslash `\` or doubled backslash `\\` is similar, slanted to the left

See also [matplotlib hatch style reference](https://matplotlib.org/stable/gallery/shapes_and_collections/hatch_style_reference.html) which this is a subset of.

## Overlapping: ordering, layers and bands

As-is, these rows have overlap: most notably since 2018 Jericho has been working for both AEW and NJPW. When drawn, the bar for AEW would hide the other almost completely. Earlier in his career there's also overlap between WCW and NJPW, but the NJPW bar will be drawn over the WCW one. If they were switched around, the NJPW bar would be completely obscured.

To help with this, two mechanisms are available: layers and bands. They are the next two optional fields, after name, orgs, start, end. Here's Jericho again, with bands:

```csv
Chris Jericho,cnwa,1991-02-01,1991-04-12
-,fmw,1991-10-10,1992-09-19
-,ecw,1996-02-02,1996-08-03
-,wcw,1996-08-20,1999-07-21
-,njpw,1997-01-04,1998-09-23,2/2
-,wwf,1999-08-21,2001-12-21
-,wwe,2001-12-21,2018-04-27
-,njpw,2018-01-04,-,1/2
-,aew,2019,05-25,-,2/2
```

This new field `band`, which is the next one after `end`, looks like a fraction, with a numerator and denominator. The denominator specifies the _total number of bands the full bar is divided into_. In this case, two bands, each half the height. There is no limit to this number, although depending on graph density higher numbers may be unreadable.

Next, the numerator specifies one or more indexes of these bands. `1/2` tells it to draw the bottom half, and `2/2` the top half. Similarly for 3 bands, `1/3 2/3 3/3` are respectively bottom, middle and top bands.
To draw more than one band at the same time, separate the numerator parts with a plus sign `+`. For example, `1+3/3` draws both the bottom and top bands at the same time.

When bands are not enough to produce a readable graph, the next optional field is layers. A layer is effectively another row where bars can be drawn, positioned below the first layer.

```csv
Chris Jericho,cnwa,1991-02-01,1991-04-12
-,wwf,1999-08-21,2001-12-21
-,wwe,2001-12-21,2018-04-27
-,njpw,2018-01-04,-,,1
-,aew,2019,05-25,-,,2
```

The last two rows here specify a layer (but omit the band). An unspecified layer is equivalent to layer `0`. Layer names are arbitrary strings, but it's convenient to use numbers. This graph will have three rows: one with the pre-2018 career, and two more full-height rows with NJPW and AEW.

## Tooltips

By default, each bar will have an on-hover tooltip that states the organization (or organizations), and date range. For example: "WCW from 1996-08 to 1999-07". This can be customized by adding yet another field after band and layer. This new field contains the tooltip text, which will be used instead of the default date range.

## Text and links

### Square-bracket delimited

Most text fields can be replaced with links. To make something a link to an article, talent, team or org page:

1. the text must be equal to the article's title. Otherwise, see below for the other method.
2. prefix the text with the article's toplevel folder, i.e. `w/` for talent pages, `o/` for organization pages etc.
3. surround the text with square brackets `[]`

This method, while simple, has many restrictions: doesn't allow for more complex links, alternate titles or linking only part of text, and cannot link to events (which have a deeper path).
However, it is quite simple, and causes the least problems with text layout, because the lengths don't change much.

```
[w/Chris Jericho]
```

### Other links

There are three more mechanisms to render links:

1. `@vline` directive supports links
2. `@legend` directive supports links
3. an explicit `@link` directive turns all matching text into links


## Directives

Directives are rows that do not define a stripe, but rather configure some other aspect of the graph, or add graphics other than bars. The rows that contain directives always start with an at-sign `@`, and contain an arbitrary number of fields, depending on their purpose.

### @vline: Vertical lines

Add vertical lines/events layer, by using the `@vline` directive. It takes three parameters: date, color and text.

```csv
@vline,2001-12-09,!black,Triple Crown
```

* this line will be positioned at the date given by `start`, and span across the whole graph
* line color will be black (given here by a named color)
* text, from the name field will be drawn vertically next to the line, using primary theme color
* end date needs to be a single dash, but is not used for anything
* the band field is left empty

For lines, the org/color field has different syntax. It takes a single color (org, named or hex), and can be followed by thickness and style. Thickness is a decimal number, and style is one of `solid` (the default), `dashed`, `dotted` or `dashdot`. These are the basic [matplotlib line styles](https://matplotlib.org/stable/gallery/lines_bars_and_markers/linestyles.html).

An additional parameter after text can be used to make this a link: just add a relative path to the article (omitting the `.md` suffix).

### @color, @legend: Custom colors and legend entries

Define a custom color (e.g. for a one-off organization) with the `@color` directive. It takes two parameters: the symbol and color definition.

```csv
@color,bjpw,!white|!red
@legend,bjpw,Big Japan Pro Wrestling
```

The name of this new color is `bjpw`, color pattern is white and red stripes. Other fields are not used, but the mandatory start and end fields must contain dashes. It can then be used in following rows. However, it should not be combined with other colors using a hatch symbol - the results of that are undefined.

Custom colors may use the same names as default organization brand colors, and override them if that's the case.

The second line adds a legend entry.

Its params are: key, which is this new color symbol; and text. Similarly to vlines, the text can be followed by another field with the link target.

### @link: Linking text

```
@link,Text to match,/link/path
```

All textual graph elements where the text **is exactly equal** to the first param, will be turned into links to the target specified in the second param. This includes:

* axis labels (names on the Y axis and dates on the X axis)
* vline labels (in addition to their own linking mechanism)
* legend elements (in addition to their own linking mechanism)

NOTE: in the future, all linking mechanisms **except this one** may be retired

### Layout options

There are several options that control the graph layout, explained below. Each of them uses the same format:

```
@option,name,value
```

* `bar_height,NUMBER` (default 0.8): controls the height of the bars. Each row (or layer) has a height of 1, so the default of 0.8 leaves some whitespace between successive rows.
* `figsize,H/W` (default: 10/5): controls the graph size in inches. The output renders the size in points, and each inch is 72 points. So the default size of 10/5 results in a width of 720pt and height of 360pt. Since the graph is always scaled anyway, this is more useful to set the graph's **aspect ratio**.
* `hide_spines,left+top+right+bottom` (default: don't hide any): spines are the sides of the rectangle that encloses the graph area. Bottom and left spines divide it from horizontal and vertical ticks respectively. The argument is a plus-separated list of spines that should be removed from the graph.
* `layout,constrained|tight` (default: constrained): selects matplotlib's layout algorithm. Notably, tight will push the legend into the graph area, but constrained will not.
* `legend,on|off` (default: on): if on, display the legend box, to the right and below the graph.
* `major_ticks,1y|2y` (default: 1y): the x-axis tick values are always years. 1y puts ticks at every year, while 2y at every other year (note: this does not mean it shows even years only).
* `minor_ticks,off|3m` (default: off): aside from major ticks, draw minor ticks every 3 months if set to that value
* `org_in_tooltip,on|off` (default: on): the default tooltip shown when hovering the pointer above a bar will include the org field (which can contain one or two orgs). If set to off, omit that and only show _from..to_ in the default tooltip. Does not apply to custom tooltips.
* `padding,number` (default: 0.4, half of default bar_height): add that much space on the y-axis above and below the first and last bars. If set to zero, these bars will touch the spines.
* `rotate_xticks,on|off` (default: off) if set to on, x-axis ticks will be rotated 90° counterclockwise.
