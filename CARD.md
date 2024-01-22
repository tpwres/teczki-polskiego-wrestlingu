# Card specification in event pages

1. The card block must be enclosed by `{% card() %}` and '`{% end %}`.
2. These start and end symbols must be on separate lines.
3. Between these symbols, the card is a [YAML](https://yaml.org) document, which must be a list.
4. Each element of that list, is itself a list of participants. The final element may be a map of options, which are useful if the match is not a simple singles match. See relevant section below.
5. The first element of that list must be the winner (or winners, if a tag team) of the match
6. Talent names in the list may be specified as either plain names like `"John Doe"`, or Markdown links to talent pages like `"[John Doe](@/w/john-doe.md)"`.
7. Linking to a non-existent page is an error, which is caught during the build process. The talent page must be created first.

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

Quotes are necessary in the inline style if an element contains spaces, or certain characters: braces `{}`, square brackets `[]`, commas `,` or colons `:`.

In block style, quotes can be omitted if an element contains spaces, but not these special characters.

The recommended style is to use block-style for the matches list, but inline-style for the individual match:

```yaml
# The following are two singles matches
- ["The Undertaker", "Giant Gonzalez"]
- ["Bob Backlund", "Randy Savage"]
```

However, nested block-style is also legal, and may be useful for multi-man matches like rumbles.

```yaml
# The following is a single match with four participants
- - The Undertaker
  - Giant Gonzalez
  - [Bob Backlund](@/w/bob.md)
  - Randy Savage
```

## Tag teams and groupings of people

In tag-team matches, we may want to list the participants as a team. To do this, separate the names with commas (and optionally spaces), and prefix them with the tag team name and a colon. Because we use a colon, quotes are mandatory in both notations here.

```
"Maki Death Kill: Maki Itoh, Nick Gage"
```

If a single side of the match contains more than one tag team, separate them with plus signs `+`:

```
"Best Friends: Chuck Taylor, Trent Beretta + Dark Order: Alex Reynolds, Evil Uno, John Silver"
```

The same notation can be used for single people added to the team

```
"FTR: Cash Wheeler, Dax Harwood + Mark Briscoe"
```

But when it's an ad-hoc team, it's fine to use commas:

```
"Hikaru Shida, Skye Blue, Willow Nightingale"
```

## Championships

When contended for, championships are listed in the options part, as described below. The champion, or team going into the match, can be marked with a `(c)` after their name. In case of tag teams, this must precede the colon.

## Options

Options may appear as the last position of the list. Options are a YAML map, which is normally written in braces `{}`. However, if only a single option is added, then braces are optional, otherwise they are mandatory.

Available options are:

- `s: STIPULATION` - if any, for example "Tables Match", "Best Two Out Of Three Falls" etc.
- `c: CHAMPIONSHIP` - the title contested. Should be a Markdown link to the organizations' page section about that title.
- `r: RESULT` - for situations like DQ or KO. Will be listed as "via RESULT". **Cannot be used together with `nc`**
- `nc: OUTCOME` - if a match did not have a clear winner, for example ended in a draw, timeout or no-contest. Will be listed as " - OUTCOME". **Cannot be used together with `r`**

Examples:

```yaml
# A title match where Toni retains
- ["Toni Storm(c)", "Skye Blue", c: "AEW Women's World Title"]
# A draw
- ["Bryan Danielson", "Adam Page", nc: "Time-limit Draw"]
# A win by disqualification
- ["Abyss", "Sting", r: "DQ"]
# A big ladder match for the tag team titles
- - "The Hardy Boyz: Jeff Hardy, Matt Hardy"
  - "Big Cass + Enzo Amore"
  - "Cesaro + Sheamus"
  - "The Club: Karl Anderson, Luke Gallows"
  - {s: "Fatal Four Way Ladder Match",c: "WWE Raw Tag Team Title"}
# A future event
- [Dawid Oliwa, Leon Lato, nc: upcoming]
```

### Special cases

Sometimes the full participants of a multi-man rumble-style match are unknown. In that case, it's sufficient to list only one, and a stipulation option. This will be presented in the results view as `Winner: Somebody`.
