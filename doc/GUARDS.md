# Guards

Guards are linters, which are code that gets ran as part of a build after each code push (or limited to GitHub pull requests). They validate the files under `content/`, helping spot some common errors and problems.

Some of these errors will then cause the build to fail either at metadata compilation stage, or later in the Zola build stage. But in both cases, error messages can be tricky to understand.

Guards produce diagnostic messages for these errors, which can be found in the build output. More recently, most of them can also add review comments on a GitHub pull request.

## Categories of guards

Guards belong in one of three top-level categories:

- card validation: mostly relevant for events, checking various parts of a `{% card() %}` block
- document validation: run on all files, check for problems in text
- markup validation: run on all files, verify if certain markup (e.g. badges) is done correctly

## List of guards

### Card/CardLinksValid

Looks at all places in a card where links may be used: opponent names, names in the crew section, championship titles, text in stipulation or segment descriptions. Checks if links used in these places are valid, that is use the correct syntax and point to existing files.

### Card/CardOptionsCorrect

Card Options refer to the parameter that can be passed to the card block, to mark it either as predicted, incomplete or unofficial. For predicted cards, we impose additional requirements: that the card section title is "Predicted card" and that all matches have the `nc: upcoming` flag.

### Card/CardSeen

Checks that the event page has one (but not both of) `{% card() %}` block or the `{{ skip_card() }}` shortcode, marking the lack of known card.

### Card/CreditsCorrect

Checks that the card has only one `credits:` entry, and that it is the last element of the card.

### Card/DelimitersCorrect

Checks that delimiter rows (`d: text, date: some-date`) are correct: text is not missing and dates are ordered chronologically (if more than one delimiter row present).

### Card/SegmentDescription

Checks that segments have a non-empty description, in one of the supported styles (either `g: text` or `g: true, s: text`).

### Card/UnlinkedChampionship

Looks at the championships at stake (the `c:` option) and ensures that championships which have their own pages are linked to them.

### Card/UnlinkedCrewmember

Checks that in the `credits:` crew block, each name that has a page is linked to it. Requires the alias list, see _Card/UnlinkedParticipant_ below.

### Card/UnlinkedParticipant

Checks that in the match opponent lists, each talent name that has a page is linked to it. Requires the alias list to be built first, so depends on other event pages to use those names too.

### Card/UnlinkedTeam

Checks that in the match opponent lists, each named team that has a page is linked to it. Similar in concept to the other Unlinked guards.

### Card/ValidCard

Validates basic properties of a card:

- that it's a non-empty list
- each element conforms to our match definition, having one or more opponents and an optional map of flags
- for a single opponent, the element must either describe a segment or have a stipulation
- checks that these flags are valid and do not conflict (e.g. can't have both `r:` and `nc:`)

### Doc/ContentLinks

Checks text in the page, finding links and ensures these point to an existing file. Similar to _Card/CardLinksValid_, but only reads paragraph text.

### Doc/EventHeaders

Checks that the structure of an event page conforms to the recommended layout, and that the header levels used are correct. The recommended structure is as follows, with level being 2 unless noted otherwise:

1. Storyline overview
2. Build-up
3. Card or Predicted card
4. Recap, at level 3
5. Highlights, at level 3
6. References

The headings are not required - they may be skipped by the author. However if present, they must follow the ordering. For example, an event page may have either a Recap or Highlights section, but they must follow Card, they cannot be after References or before Card.

### Markup/BadgesValid

The `{{ org_badge() }}` shortcode is sometimes confusing to use, with its two allowed notation. This guard checks for common mistakes in its use and recommends corrections.
