# Articles

TPW's articles (under `a/`) represent any piece of content that is not about a tracked event (these go under `/e`), person or team/faction (`w/` and `tt/`), organization (`o/`), venue (`/v`), or a championship title (under `c/`).

Articles typically use the `article.html` template, which is a generalist document-like template with no extra features like pagination. However, most markup and blocks like `{% card() %}` will continue to work inside articles. Notably, image galleries work in articles same as everywhere else.

The main list under `a/` shows all articles, sorted alphabetically by title, plus a collapsed list of categories by default.

## Cover image

By default, articles do not have a cover image, and a generic image based on the site logo is used on the article list. Otherwise, the first image defined in a gallery, or specifically its thumbnail, is used as a cover image on the article lists.

The same image is also used for the automatic thumbnail (messaging and social media embed), same as for all other pages.

## Categories

Articles may be assigned to a category. A category is assigned with a `category` taxonomy, and is a capitalized term that may include spaces.

```toml
[taxonomies]
category = ["History"]
```

An article MAY be assigned to more than one category if needed, but that should be rare. When not assigned, it will only show in the main list.

Each term used in this taxonomy (a category name) MUST have a corresponding folder under `a/`.
That folder is technically a Zola Section, containing at least a single `_index.md` file to define it.
Following the previous example, this would be `a/history/_index.md`.
If the category term includes spaces, they must be replaced with a single dash each, for example a category named `Wrestling Moves` would need `a/wrestling-moves/_index.md`.

The contents of this file are a minimal, front-matter only section definition. The section MUST use the `articles/category.html` template, and its title MUST be the same as the term. For the History section, it should look like the following example.

```
+++
title = "History"
template = "articles/category.html"
+++
```

When correctly defined, this new section can be accessed at `/a/SECTION-NAME` and presents a list of articles in that category only, plus a collapsed list of categories. It is an error if an article specifies a category that does not have a correctly populated folder.

### Category list

The list of categories is a `<details>` disclosure element, that starts collapsed, only showing the label **Categories**. When expanded, it shows a simple list of links to the category sections, plus the article count in each.

When presented on the main list, all items will be links. But when presented on a category page, the current category is replaced with static text, and the page title is changed appropriately.

## Placing articles in category folders

Article files may be located either in the top level articles folder `a/`, or inside one of the section folders. When inside section folders, any links to them must use the full path `@/a/section/article.md`. When moving articles, remember to provide alias paths matching the older location.

Placing an article in a category folder DOES NOT automatically make it belong to that category, a taxonomy entry is still needed. It is not an error (but may be confusing) if an article declares a different section than the folder it is placed in.

## Sorting

In the main list and each category, articles are sorted by their last-updated date, newest first. This is normally provided in the article's front matter, but that field is unused and discouraged.
Instead, a script running as part of the build process fills this info from the version control system.

This is controlled by two entries in the relevant `config.toml`, in the `[extra.articles]` section.

1. `sort_by = "FIELD"`, where FIELD is any page field that can be used for sorting. The most useful values are `title`, `slug` (to sort ignoring case) and `updated`.
2. `reverse = false`, but when set to true, reverses the sorted order. This is necessary when sorting by last-updated.

The two settings are however different between the live site and running a dev server locally. As described above, the articles do not provide the last updated date. Sorting by `updated` will cause an error and prevent running the server. To remedy that, the local dev config file specifies sorting alphabetically by title, which will never cause an error.
