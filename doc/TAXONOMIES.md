# Taxonomies

TPW makes use of Zola's [taxonomies](https://www.getzola.org/documentation/content/taxonomies/).
They are chiefly used for pagination, but also for some extra info about the talent.

## General usage

Taxonomies can be added to any page, in the front matter block. Read `FRONT-MATTER.md` to learn more about this block. They must be put in their own section `[taxonomies]`.
Each row in that section is of the form `<taxonomy_name> = ["<term1>", "<term2>"]`.
While there is no technical limit to how many terms can be used, some of the taxonomies only make use of the first term.
Taxonomy name must be one of the defined taxonomies, as defined in `config.toml`. It is an error to assign terms to an unknown taxonomy.

## Country

The simplest taxonomy, applying only to talent pages. Terms are ISO-3166 country codes, two-letter long.
For most countries, they are equivalent to their [country code top level domain](https://en.wikipedia.org/wiki/Country_code_top-level_domain), except for Great Britain where the code is `GB` but the ccTLD is `.uk`.
Terms may be written in uppercase or lowercase, but uppercase is preferred.
For uncommon countries, a comment can be added after the entry, preceded with `#`, and stating the full English name of the country.

Only the first term in that list will be used, displaying a flag next to the talent's name in several places.
On their talent page, if they have one, it will show on the right of the title.
On the alphabetical talent list it will show to the left of their name.
In the All-Time Roster section of an organization's page, it will show to the left of their name.


### Example

```toml
+++
title = "Ron Corvus"
template = "talent_page.html"
[taxonomies]
country = ["HU"] # Hungary
```

### Semantics

The flag should match the talent's preferences, i.e. be the same as the country they are billed from, when appearing internationally.
Otherwise, their country of birth is preferred. It can be gleaned from Cagematch, in the Birthplace field of the wrestler's bio.

## Chronology and chrono_root

The two taxonomies are linked together, and used for pagination.
At the bottom of each event page, there are links to preceding and following events held by the same organization, and sometimes to events belonging to additional categories, but still preceding and following the event described.

The first taxonomy, `chronology` applies only to event pages.
Its allowed terms are, technically, the same ones as for `chrono_root`. 

### Organization's event timeline

An easier way to understand it is to first restrict terms to organization names.
An event belongs to an organization's chronology if it names the organization in its `chronology` taxonomy.

#### Example

```toml
+++
title = "PpW Ale Grzeje"
template = "event_page.html"
[taxonomies]
chronology = ["ppw"]
```

This event will now be listed in PpW's events section.
At the bottom of its page, there will be links to preceding and following events that also carry a `chronology = ["ppw"]` taxonomy.

### Creating additional chronologies

Some events may want to be listed as part of more than one chronology. For example, PTW's Underground series of events makes its own chronology. In that case, events from that series can list two items in their `chronology`.

#### Example

```toml
+++
title = "PTW Underground 6"
template = "event_page.html"
[taxonomies]
chronology = ["ptw", "underground"]
```

This event will be listed in PTW's events section.
At the bottom of its page, there will be links to preceding and following events that also carry a `ptw` taxonomy, but also a separate set of links to preceding and following events carrying the `underground` taxonomy.

This is where the second taxonomy is useful.

### `chrono_root`

Each of the bottom pagination sections has a header line, that names the chronology. This header line can also display a link to any page, if that page carriers a `chrono_root` taxonomy with the same value.
This is actually how the organization event lists are implemented: each organization page has a `chrono_root` with its name.

#### Example

```toml
+++
title = "Prime Time Wrestling"
template = "org_page.html"
[taxonomies]
chrono_root = ["ptw"]
```

With this setup, all PTW events will have pagination, with a header line that reads "Prime Time Wrestling event chronology", and "Prime Time Wrestling" will link to the organization page.

This taxonomy is not restricted to organization pages. Any page can be a chronology root. One example in use is the page for Poznań International Fair, which hosted events by both PpW and KPW (as part of Pyrkon).

### Chronologies without a root page

Chronologies can also exist without a page having the corresponding `chrono_root`. In that case, the header text will not link to anything.
However, one more thing must be defined: the expansion text that replaces the keyword (which is normally replaced with the page title).
These are defined in `config.toml`, in the `[extra.chronology]` section:

```toml
[extra.chronology]
underground = "PTW Underground"
godzina-zero = "KPW Godzina Zero"
arena = "KPW Arena"
pyrkon = "Pyrkon"
```

Finally, if a chronology is used that does not have a chrono_root page, and is missing the expansion text, it will still work.
However, its header will be displayed with multiple exclamation marks and in bold to emphasize it's misconfigured.

## Venue

This taxonomy applies only to event pages, and links events to their venue page.
The allowed term values here are filename roots (filename minus the `.md` extension) of pages under `content/v/`, which is the directory for venue pages.

The venue page has a list of events as well, and this list shows exactly all the events that have a matching `venue` taxonomy term.


#### Example

```toml
+++
title = "PTW Underground 6"
template = "event_page.html"
[taxonomies]
venue = ["ptw-targowa"]
```

This event will be listed on the venue page for PTW Performance Center.
The venue is not linked automatically on the event's page. Instead, it should be linked in the descriptive text.
