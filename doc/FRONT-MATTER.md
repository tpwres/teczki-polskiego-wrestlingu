# Front matter

Each document begins with a front-matter block, which begins and ends with three plus signs `+++` on a line of their own.
The front matter contains important properties of the document, as well as things like taxonomies (see `TAXONOMIES.md`) and the gallery or manifest (see `GALLERY.md`).
The contents of a this block are parsed as [TOML](https://toml.io/en/).
Some settings must be specified in the top-level section, that is before any other sections like `[extra]` or `[taxonomies]`.

## Mandatory

Certain entries are mandatory for all files, and not including them is an error.

* `title`: The document's title, as displayed by your browser, Atom feeds and in link previews. Must be at top-level.
* `template`: Template to use, depends on the section. Which templates should be used where is explained below. Must be at top-level.

## All pages

* `authors`: An array of author names. These are displayed in the footer, and used in Atom feeds. Must be at top-level.
* `description`: Optional, short textual description, used in social media previews and indexed by search engines. If omitted, the page's first paragraph is used instead.
* `[taxonomies]`: The page's taxonomies, including chronology and venue for events, and country for talent. Explained in their own document `TAXONOMIES.md`.
* `[extra]`: Additional section, most importantly containing the gallery (see `GALLERY.md`). Certain pages may make use of settings in this section, which are specified here `extra.some_setting`. In the file, this notation means that there is an `extra_setting` key below the `[extra]` section.
* `extra.toclevel`: If present, a table of contents is automatically inserted at the beginning. Documented in `TOC.md`.

## Event page

* `template`: Must be `event_page.html`.
* `extra.toclevel`: Not supported yet.
* `extra.city`: If present, describes the city or cities where the event venue is located. Displayed on the homepage listing (e.g. 'Warszawa, Mińska 65'), and in an event's header above its date and name. May be a single quoted string, like `"Warszawa"`, or an array of these, for example `["Gdańsk", "Sopot"]`. If the latter form is used, they will be displayed joined by slash characters: 'Gdańsk / Sopot'.
* `extra.hide_results`: If present and set to `true`, the card block will not display results. Useful for upcoming events, and past events where the match outcomes are unknown.

## Talent page

* `template`: must be `talent_page.html`.
* `extra.omit_career`: if present and set to `true`, skips the career match listing. Useful for non-wrestler talent.

## Team page

* `template`: must be `team_page.html`.
* `extra.omit_career`: if present and set to `true`, skips the career match listing.
* `extra.orgs`: an array of organization abbreviations. If present, their logos are displayed in the page's header, similar to how a country flag may be displayed on a talent page.

## Org page

* `template`: must be `org_page.html`.
* `extra.hide_events`: if present and set to `true`, skips the event list section.
* `extra.hide_roster`: if present and set to `true`, skips the all-time roster section.
* `extra.compact_event_list`: if present and set to `true`, uses a more compact event list format, without dividing the list into per-year sections. A compact list also will not automatically produce an "Upcoming" section.

## Venue page

* `template`: must be `venue_page.html`.

## Article

Template should be `article.html`.
