This folder contains SASS stylesheets, split by purpose. It is reusable for subsites of TPW: just copy the components you need, create a main stylesheet that imports them, and point your style directive to that. Since most subsites will only need a subset of these, it lends itself to faster page load.

## Components

* `articles`: article list and TOC (for all pages that use it).
* `card`: event card tables, free-card.
* `career`: career match list, yearly stripes.
* `championship`: championship table as used in org articles.
* `controls`: all form controls. Some basic ones (input + button) are included in `layout` too.
* `events`: event listing (CM-style and plain), some elements of the event pages.
* `gallery`: in-article galleries, including fallback non-js zoom.
* **`gruvbox_colors`**: the color palettes used. No need to import directly - this is used by `theme`.
* `icons-badges`: base styles for Feather/Lucide icons, and for org badges.
* **`layout`**: base grid, layout and non-specialized table.
* `lightbox`: dialog-based lightbox UI for browsing photos.
* **`nav`**: navigation and footer.
* `pagination`: taxonomy-based pagination, used on event pages.
* `search`: search UI.
* `special`: one-off styles for certain articles.
* `talent`: talent lists, both main and per-org, plus some elements of a talent's page.
* **`theme`**: dark and light themes.
* `timeline`: styles for event recap timelines.
* **`typography`**: fonts and text colors.

Components marked in **bold** are required.
