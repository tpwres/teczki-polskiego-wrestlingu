# Card specification in event pages

1. The card block must be enclosed by `{% card() %}` and '`{% end %}`.
2. These start and end symbols must be on separate lines.
3. Between these symbols, the card is a [YAML](https://yaml.org) document, which must be a list.
4. Each element of that list, is itself a list of participants. The final element may be a map of options, which are useful if the match is not a simple singles match. See relevant section below.
5. The first element of that list must be the winner (or winners, if a tag team) of the match.
6. Talent names in the list may be specified as either plain names like `"John Doe"`, or Markdown links to talent pages like `"[John Doe](@/w/john-doe.md)"`.
7. Linking to a non-existent page is an error, which is caught during the build process. The talent page must be created first.
8. In the rare event that an event intentionally has no card (mostly for upcoming events), replace the card block with `{{ skip_card() }}`.

`{% card() %}` may also indicate that the card is unofficial, predicted or incomplete. This is done by passing exactly one of `predicted=true`, `unofficial=true`, `incomplete=true`, for example:

```
{% card(incomplete=true) %)}
```

When using `predicted=true`, the event page will not display match results. This is alternatively accomplished with the `hide_results` setting in front-matter block.

## YAML lists

A YAML list is expressed either block-style:

```yaml
- element1
- element2
- element3
```

or inline-style:

```yaml
["element1", "element2", "element3"]
```

Quotes are necessary in the inline style if an element contains spaces, or certain characters: braces `{}`, square brackets `[]`, commas `,` colons `:`, apostrophes/single quotes `'` or double quotes `"`.

In block style, quotes can be omitted if an element contains spaces, but not these special characters. If unsure, prefer quotes as they're always safe.

The recommended style is to use block-style for both the match list, and individual matches.

```yaml
# The following are two singles matches
- ["The Undertaker", "Giant Gonzalez"]
- ["Bob Backlund", "Randy Savage"]
```

However, nested block-style is most readable, and the recommended way to note all matches.

```yaml
# The following is a single match with four participants
- - The Undertaker
  - Giant Gonzalez
  - '[Bob Backlund](@/w/bob.md)'
  - Randy Savage
```

## Tag teams and groupings of people

In tag-team matches, we may want to list the participants as a team. To do this, separate the tag member names with ampersands (`&`), and prefix them with the tag team name and a colon. Because we use a colon, quotes are mandatory in both notations here.

```
"Maki Death Kill: Maki Itoh & Nick Gage"
```

If a single side of the match contains more than one tag team, separate them with plus signs `+`:

```
"Best Friends: Chuck Taylor & Trent Beretta + Dark Order: Alex Reynolds, Evil Uno, John Silver"
```

The same notation can be used for single people added to the team

```
"FTR: Cash Wheeler & Dax Harwood + Mark Briscoe"
```

When it's an ad-hoc team without the name, also use ampersands:

```
"Hikaru Shida & Skye Blue & Willow Nightingale"
```

Note: The same notation should be applied in entries for the [Tag Team Championships](https://tpwres.pl/c/).

## Roles in the match

Except for segments, each side has at least one fighter in the match. Often, additional people should not be counted as fighters, but rather as valets or managers. To denote a manager, use a semicolon `;` or `w/` before their name. For example, here are two equivalent ways to note a team of two plus a manager.

```
Cash Wheeler, Dax Harwood; Tully Blanchard
Cash Wheeler, Dax Harwood w/ Tully Blanchard
```

When multiple people have the same role, ampersands can be used instead of repeating the other symbols. A person that is listed **after** an ampersand will have the **same role** as the person listed **before**. For example:

All three fighters:

```
Matt Hardy, Jeff Hardy, Johnny Hardy
Matt Hardy, Jeff Hardy & Johnny Hardy
Matt Hardy & Jeff Hardy & Johnny Hardy
```
(Note: this might clash with the tag team notation using ampersands, as outlined above. Use with caution.)

Multiple managers:

```
Galeno Del Mal w/ Hijo del Dr. Wagner & Silver King
```

## Championships

When contended for, championships are listed in the options part, as described below. The champion, or team going into the match, can be marked with a `(c)` after their name. In case of tag teams, this must precede the colon.

## Options

Options may appear as the last position of the list. Options are a YAML map, which is normally written in braces `{}`. However, if only a single option is added, then braces are optional, otherwise they are mandatory.

Available options are:

- `s: STIPULATION` - if any, for example "Tables Match", "Best Two Out Of Three Falls" etc.
- `c: CHAMPIONSHIP` - the title contested. Should be a Markdown link to the organizations' page section about that title.
- `r: RESULT` - for situations like DQ or KO. Will be listed as "via RESULT". **Cannot be used together with `nc`**
- `nc: OUTCOME` - if a match did not have a single, clear winner, for example ended in a draw, timeout or no-contest. Will be listed as " - OUTCOME". **Cannot be used together with `r`**. If the result is unknown, use `nc: ?`. For matches that have been announced for future events and haven't happened yet, use `nc: upcoming`, which will be shown as `Upcoming: ` before the match details.
- `g: true` - marks this entry as a se`g`ment, not a match. Useful to mark someone's participation that was not a match, because it gets counted towards their years active and the organization's all time roster. When this is present, `nc` and `r` are ignored, but `c` and `s` will still be displayed.
- `g: SEGMENT DESCRIPTION` - same as above, but text is displayed in the details column. Both this text and stipulation will be displayed, although stipulation should be left empty.
- `n: TEXT` or `n: [list, of, texts]` - adds notes, which are displayed in a smaller font below the participants. Notes are only visible on event pages, and only when "toggle results" was clicked.
- `x: [n]` - e`x`cludes person number `n` from the talent list. Useful when a non-worker makes a one-off appearance, eg. as a guest in a promo segment. Can take more than one number, e.g. `x: [1,3]` to exclude first and third.

## Special rows

A special row in the card has no opponents, but only options. The list of available options is different for special rows.

- `d: DELIMITER TEXT` - inserts a `d`elimiter row. Provided text will be centered across the whole width of the table, in a bold font. **Match numbering restarts after a delimiter.**
- `date: YYYY-MM-DD` - changes the date for matches that follow it in the list, used for multi-day events that have a single page. Does not render in the list if used on its own, and can be combined with a delimiter row.
- `credits: CREDITS` - adds an invisible row, that won't be included as part of the match card, but listed below it in a section called "Cast and crew"

Examples:

```yaml
# A title match where Toni retains
- ["Toni Storm(c)", "Skye Blue", c: "AEW Women's World Title"]
# A draw
- ["Bryan Danielson", "Adam Page", nc: "Time-limit Draw"]
# A win by disqualification
- ["Abyss", "Sting", r: "DQ"]
# A big ladder match for the tag team titles
- - "The Hardy Boyz: Jeff Hardy & Matt Hardy"
  - "Big Cass + Enzo Amore"
  - "Cesaro + Sheamus"
  - "The Club: Karl Anderson & Luke Gallows"
  - s: "Fatal Four Way Ladder Match"
    c: "WWE Raw Tag Team Title"
# A future event
- [David Oliwa, Leon Lato, nc: upcoming]
# A promo segment, many possible notations
- [Lita, Edge, { g: true, s: Live Sex Celebration}]
- - Lita
  - Edge
  - g: true
    s: Live Sex Celebration
- - Lita
  - Edge
  - g: Live Sex Celebration
# A delimiter marking Day 2 of the event
- d: 'Day 2'
# Change date for the next set of matches. Do not use quotes for the date.
- date: 2024-11-19
# Combining delimiter with a new date, two possible notations.
- d: 'Day 3'
  date: 2024-11-19
- { d: 'Day 3', date: 2024-11-19 }
# Excluding a person from the talent list
- - 'Leonardo'
  - 'Rafaello'
  - 'Donatello'
  - 'Michaelangelo'
  - 'Picasso'
  - g: Cowabunga dude!
    x: [5] # Excludes Picasso
# Cast credits for a show
- credits:
    Referees: Aubrey Edwards, Red Shoes
    Ring announcer: Justin Roberts
```

### Special cases

Sometimes the full participants of a multi-man rumble-style match are unknown. In that case, it's sufficient to list only one, and a stipulation option. This will be presented in the results view as `Winner: Somebody`.

### Credits row

The contents of this row is a YAML map, which should normally be written in block style, that is indented one level more than the `credits` keyword, and with each pair on its own line.
The map keys are roles, for example "Referee", "Ring announcer", "General Manager". There is no fixed list of roles, use what's appropriate.
The values are names, or lists of names, which work similarly to opponent names in matches. Names can be Markdown links to the respective person's page.
This feature is also useful for listing all notable personnel present at an event, but did not participate in matches or segments.
