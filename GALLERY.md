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

Each page that has a gallery signifies it by having an `[extra.gallery]` section in the front matter. Using Ale Grzeje for illustration:

```
+++
title = "PpW Ale Grzeje"
template = "event_page.html"
[extra]
venue = "teatr-komuna"
[extra.gallery]
1 = { path = "ale-grzeje-poster.jpg", caption = "The show's official poster. Top photo shows [Gustav Gryffin](@/w/gustav-gryffin.md) standing face to face with [Biesiad Strong](@/w/biesiad.md). The bottom one has Jakob Sigmarsson and [Rafi](@/w/rafi.md) celebrating Gustav's victory.", source = "Facebook PPW Ewenement"}
+++
```

Other entries in this front matter are out of scope here. The gallery section contains any number of key-value pairs.
The key ("1" in the above example) is any alphanumeric string without whitespace. It can be just a number, as in this example,
but need not be.
The value is always a map (another list of key-value pairs), which **must contain at least path and caption**.

* `path` must name a file in the page's images folder (see above). There is no way to link images from other articles, and copying them is the only solution for now.
* `caption` is the text to display under the thumbnail in the gallery grid. Markdown can be used in this text, as shown in the example, so it can link to other pages. However, shortcodes and template markup cannot be used.
* `source` is the attribution. While currently it's not displayed, we still want to collect it to have a grasp on where the images came from.

### Rules for documenting atribution

* If it's a screenshot from social media, note the platform and the profile or page, e.g. 'Instagram @some_profile_name', or 'Twitter/X @thisorthatperson'.
* If it's your own photo taken at an event, add your name or preferred nickname, e.g. 'Photo by John Anon'.
* Photos from other online media (portals, news sites, forums) should at least note the source name, e.g. 'Gazeta Pomorska', and possibly a link to the resource they came from (unless it's also linked in the article as reference). If the photos include visible watermarks, include that in the attribution, e.g. 'John Anon Photos'.

### Image formats

Acceptable image formats are `jpg`, `png` and `webp`. This list may be expanded in the future.

The formats should be used appriopriately. PNG is best for screenshots containing mostly text, JPG is best for photos or screenshots that are primarily not text (e.g. have a rich background), and WebP is a generic format that can handle both of these roles.
If used wrongly, file size grows or quality degrades: PNG can encode photos but takes much more space than JPG. JPG can encode text, but suffers from artifacts.

For any image, its thumbnail (located in the `tn/` subdirectory) must be encoded in the same format.

## Videos?

Currently, there is no provision to host or display videos on the site. While embedding other sources like YouTube is feasible, this goes against the intended goal of archiving and hosting all the content ourselves. Therefore, videos can currently only be links to another site.

Another reason for not hosting videos is to avoid copyright issues, especially with organizations that are still active.
This is not a site to host videos of recent events, but an archive/time capsule of the scene.
