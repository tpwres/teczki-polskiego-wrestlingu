# Geography

Files under the venues directory (`content/v`) may define additional geographical info, to be displayed on a map. There are two ways to achieve this: within the file itself, or with a GeoJSON file.

## Map-ready documents

To be represented on the map, the document only needs to include two things in its frontmatter (see `FRONTMATTER.md`): the `[extra.geo]` section and `coordinates` within that section.

```toml
+++
title = "My Backyard"
template = "venue_page.html"
[extra]
city = "Zakrzówek"
[extra.geo]
coordinates = '50.94648/22.37915'
+++
```

Coordinates are listed in the order of longitude, latitude, separated with either a comma or a slash `/` like presented here. This format was chosen to simplify copying coordinates from existing map services. Notably, it is the inverse of what GeoJSON uses.

This document can now be represented on a map. It will use the default presentation, which is:

* a default pin type
* hovering over that pin will show the venue name (title) only
* clicking will open a popup, which will contain the name, as a link to its page

### Type and description

An optional `type` key in the `[extra.geo]` section changes which pin type is displayed.
Currently, the defined types are:

* `venue` - default pin
* `historical-venue` - pin representing a no-longer used venue
* `important-venue` - pin representing a significant venue, which may be the main or home venue.
* (unspecified) - same as `venue`, default pin

More types may be added in the future.

To change the text, include a `description` key in the `[extra.geo]` section, with a text value. This text supports some Markdown - text formatting and links, mostly. Note that reference-style linking (with a table of list at document end) is not supported here. Use the same syntax to link to other internal pages as elsewhere.

### Orgs

The popup can also include one or more org badges. Add `orgs` to the `[extra.geo]` section, with a value that is an array of org shortcuts. For example:

```toml
[extra.geo]
orgs = ['ptw', 'mzw']
```

### Marker color

* If no organizations were specified for a document, it will use a neutral color presentation (e.g. white).
* If `orgs` were specified, and it is a list of exactly one item, the marker will use that organization's color scheme, if defined.
* If organizations has two or more items, the marker will also use a neutral color presentation.

## GeoJSON

The second way to add content to the map is by putting GeoJSON files in the same directory. A GeoJSON file is a JSON-formatted document that contains either a single `Feature` or a `FeatureCollection`. Refer to appropriate documentation to learn more about GeoJSON.

To add a single pin to the map, the feature should have a geometry type of `Point`, which will place a default pin in the coordinates given. All GeoJSON feature types are supported, but currently only Point adds hover text and popup.

There is no requirement for a GeoJSON file to be associated with a venue page. The two types of documents are completely independent of each other. Care must be taken to not duplicate content, or to create an unreadable map by stacking pins too close.

### Properties

Features may have a `properties` key, which is a map containing arbitrary key-value pairs. Some of these pairs can be used to configure the pin style, hover text and popup content. Mostly they correspond one-to-one with keys from the `[extra.geo]` section described above .

* `type`: defines pin types
* `name`: hover text, equivalent to `title`. Plain-text only, no Markdown.
* `description`: popup text, handles Markdown.
* `orgs`: Orgs list

All other keys (possibly inherited from mapping software) are ignored.

Note that in JSON documents, newlines are not permitted inside strings, and there is no alternative notation for long strings. Therefore, newlines must be represented with `\n` escapes.

### Example

Here's a GeoJSON document which collects all the mentioned features, and replicates the front-matter example.

```json
{
    "type": "Feature",
    "geometry": {
        "type": "Point",
        "coordinates": [22.37915, 50.94648]
    },
    "properties": {
        "name": "My Backyard",
        "type": "venue",
        "description": "An example venue location",
        "orgs": ["ptw", "mzw"]
    }
}
```
