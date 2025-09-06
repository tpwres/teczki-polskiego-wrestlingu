# Page galleries

Some page types can have image galleries attached. Currently, these are talent pages, event pages and organization pages.
This list is not exhaustive, and support for galleries can be added to other pages, even on a one-off basis.

The images are hosted on a dedicated CDN, which is available under the `i.tpwres.pl` domain. The details of that,
and how to add new images are out of scope here.

## Directory structure

Images are kept in a directory that matches the path of the page they are published on. For example:

* PTW has its page under `/o/ptw`. Images to be shown there must be in a folder also called `/o/ptw`.
* Justin Joy's article has many photos and screenshots. The path to his article is `/w/justin-joy`, and so is the folder that contains these photos: `/w/justin-joy`
* A given event like PPW's Ale Grzeje lives under its organization's events subfolder `/e/ppw/`, followed by the event's date `2024-07-13`, then the organization names involved `ppw`, and the event's title. Together this makes `/e/ppw/2024-07-13-ppw-ale-grzeje`, and this is also the attached images' folder path.

Under each image folder, there must also be a `tn/` folder. Files in that folder are thumbnails. They must use the exact same filename as their original version. Thumbnails are created by cropping and scaling the image to a size of 300x300.

## Gallery notation

Each page that has a gallery signifies it by having an `[extra.gallery]` section in the front matter (or manifest file, see below). See `FRONT-MATTER.md` for more on the front matter block. Using Ale Grzeje for illustration:

```
+++
title = "PpW Ale Grzeje"
template = "event_page.html"
[extra]
venue = "teatr-komuna"
collapse_gallery = true
[extra.gallery]
1 = { path = "ale-grzeje-poster.jpg", caption = "The show's official poster. Top photo shows [Gustav Gryffin](@/w/gustav-gryffin.md) standing face to face with [Biesiad Strong](@/w/biesiad.md). The bottom one has [Jakob Sigmarsson](@/w/jakub-linde.md) and [Rafi](@/w/rafi.md) celebrating Gustav's victory.", source = "Facebook PPW Ewenement"}
+++
```

Other entries in this front matter are out of scope here. The gallery section contains any number of key-value pairs.
The key ("1" in the above example) is any alphanumeric string without whitespace. It can be just a number, as in this example,
but need not be.
The value is always a map (another list of key-value pairs), which **must contain at least path and caption**.

* `path` must name a file in the page's images folder (see above). There is no way to link images from other articles, and copying them is the only solution for now.
* `caption` is the text to display under the thumbnail in the gallery grid. Markdown can be used in this text, as shown in the example, so it can link to other pages. However, shortcodes and template markup cannot be used.
* `source` is the attribution. While currently it's not displayed, we still want to collect it to have a grasp on where the images came from.
* `skip_art` (optional). If present and set to true, this image will be excluded from Artwall. Recommended to set for photos that are low-resolution, or screenshots containing mostly text.

### Collapsing

The extra section may contain a key named `collapse_gallery`. Depending on its value, the gallery may be collapsed:

* when set to `true`: gallery is always collapsed, only showing the first six thumbnails, and a link to display the rest.
* when set to `"auto"`: gallery is only collapsed if it has more than 12 items
* when set to `false`: gallery is never collapsed
* when the key is missing: same as `"auto"`

Regardless of whether the gallery is collapsed or not, the lightbox can navigate between all photos without expanding it first.

### Alternate TOML format

The TOML format used in the front matter offers some flexibility. The same gallery can also be rewritten as:

```toml
[extra.gallery.1]
path = "ale-grzeje-poster.jpg"
caption = "The show's official poster. Top photo shows [Gustav Gryffin](@/w/gustav-gryffin.md) standing face to face with [Biesiad Strong](@/w/biesiad.md). The bottom one has [Jakob Sigmarsson](@/w/jakub-linde.md) and [Rafi](@/w/rafi.md) celebrating Gustav's victory."
source = "Facebook PPW Ewenement"
```

Notice the changes: key is now in square brackets, prefixed by `extra.gallery`. Each required map item is now on a separate line, and no commas are necessary to separate them.

This format also allows multiline text, most useful for captions. To do so, use the triple-quoted long string notation, and escape the newline with a backslash. Reusing the same example:

```toml
[extra.gallery.1]
path = "ale-grzeje-poster.jpg"
caption = """\
  The show's official poster.
  Top photo shows [Gustav Gryffin](@/w/gustav-gryffin.md) standing face to face with [Biesiad Strong](@/w/biesiad.md).
  The bottom one has [Jakob Sigmarsson](@/w/jakub-linde.md) and [Rafi](@/w/rafi.md) celebrating Gustav's victory.
"""
source = "Facebook PPW Ewenement"
```

However, line breaks will not be preserved in the displayed text, unless `<br>` is used to force them.

### Rules for documenting attribution

* If it's a screenshot from social media, note the platform and the profile or page, e.g. 'Instagram @some_profile_name', or 'Twitter/X @thisorthatperson'.
* If it's your own photo taken at an event, add your name or preferred nickname, e.g. 'Photo by John Anon'.
* Photos from other online media (portals, news sites, forums) should at least note the source name, e.g. 'Gazeta Pomorska', and possibly a link to the resource they came from (unless it's also linked in the article as reference). If the photos include visible watermarks, include that in the attribution, e.g. 'John Anon Photos'.

### Image formats and sizes

Acceptable image formats are `jpg`, `png` and `webp`. This list may be expanded in the future.

The formats should be used appriopriately. PNG is best for screenshots containing mostly text, JPG is best for photos or screenshots that are primarily not text (e.g. have a rich background), and WebP is a generic format that can handle both of these roles.
If used wrongly, file size grows or quality degrades: PNG can encode photos but takes much more space than JPG. JPG can encode text, but suffers from artifacts.

For any image, its thumbnail (located in the `tn/` subdirectory) must be encoded in the same format.

As a rule of thumb, images above 250KiB in size should probably be converted to a more appropriate format (this is mostly applicable to screenshots). If they already are in that format, they should be scaled down and optimized until they reach that size.
There is no recommended resolution for images, use the highest one that looks good and fits under the size.

## Manifest file

**Instead of** listing each photo in the front matter section, pages may specify that they use a manifest file instead.
This is useful for pages with more than a couple of photos.

```toml
[extra.gallery]
manifest = "@/e/low/2024-12-01-low-1-gallery.toml"
```

A manifest file is just a text file in a supported format, typically TOML, that lists the photos in a similar way to the frontmatter section. A single page may have **either** a manifest **or** a photo listing in the front matter. Combining the two is unsupported.

The value of the `manifest` key is a path to the manifest file, which is resolved in the same fashion as all other internal links.
It is recommended to keep the manifest file in the same directory with its page. In the example above, the manifest acoompanies an event page, and is accordingly put in the `e/low` directory.

The manifest file should have the following structure:

```toml
[KEY]
path = "filename.jpg"
caption = "Lorem ipsum dolor sit amet."
source = "Max Mustermann"
[KEY2]
path = "filename2.webp"
caption = "Consectetur adipiscir elit."
source = "Max Mustermann"
```

The `path`, `caption` and `source` fields work exactly as described under [Gallery notation](#gallery-notation) above.
`KEY` is any alphanumeric string, also described in that section, and can be any arbitrary string. However, for large galleries accompanying event pages, there's a recommended schema for keys, to help sort and maintain them.

### Recommended schema for event pages

1. All photos will be using a four-digit key `MMXX`. The first two digits (`MM`) indicate the match or segment in the card, and the last two form a sequential number starting with `01`.
2. Posters, photos of the venue, anything not showing in-ring action should use `00` or `99` as the first two digits. Use `0000` for the main show poster, `00xx` for other posters and venue photos. If the photos should instead be sorted towards the end, use `99xx`.
3. Photos related to matches and segments should use the match or segment's number for the first two digits. The first match or segment is therefore `01xx`.
4. Entries in the front matter or manifest should be sorted by key. The order of the photos is always exactly as listed, no sorting is done before displaying the gallery.

## Automatic thumbnail

Many social media platforms and messaging apps try to show rich previews of links shared through them. This is done by the pages providing specific metadata, which includes a thumbnail.
Any page with a gallery will have such a thumbnail, **taken from the first photo listed** in the gallery or manifest, regardless of its key.

* For event pages, the show poster should always be placed first.
* For talent pages, the first photo should be a usable portrait of the person, preferably showing their face.
* Venue pages can use a photo of the front entrance, or a recognizable sign or logo.
* Other pages, such as articles, have no specific requirements, but should select at least an interesting and relevant photo.

## Videos?

Currently, there is no provision to host or display videos on the site. While embedding other sources like YouTube is feasible, this goes against the intended goal of archiving and hosting all the content ourselves. Therefore, videos can currently only be links to another site.

Another reason for not hosting videos is to avoid copyright issues, especially with organizations that are still active.
This is not a site to host videos of recent events, but an archive/time capsule of the scene.

## Other files like PDFs?

This is under consideration, however most likely it will be simpler than galleries. Files like that will simply be downloadable from the site, without displaying any thumbnails.
