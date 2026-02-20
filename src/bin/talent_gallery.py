import argparse
from content import ZipContentTree, FilesystemTree
from typing import cast, Any, TypedDict, Optional
from functools import singledispatch
from itertools import chain
from page import EventPage, TalentPage, Article, OrgPage, Page, VenuePage
from page import all_talent_pages, page, pages_under
from pathlib import Path
import tomllib, re, json

class GalleryItem(TypedDict):
    path: str
    caption: str
    source: Optional[str]

def load_manifest(manifest_path, zola_path = True, verbose = True) -> dict[str, GalleryItem]:
    """Given a manifest path, resolve it and load content as TOML."""
    content_path = Path.cwd() / 'content'
    resolved_path = Path(manifest_path.replace('@', str(content_path))) if zola_path else manifest_path
    if verbose:
        print(f"Loading manifest from {resolved_path}")

    # Should support other formats, but TOML is the de-facto standard
    return tomllib.load(resolved_path.open('rb'))

def load_gallery(fm: dict[str, Any], path: Path, verbose = True) -> Optional[dict[str, GalleryItem]]:
    """Load gallery from the provided front matter. Accepts galleries with manifests."""
    extra = cast(dict[str, Any], fm.get('extra', None))
    if not extra: return None

    gallery = cast(dict[str, GalleryItem], extra.get('gallery'))
    if gallery is None:
        # Pass through empty dict
        return None

    if (manifest := gallery.get('manifest')):
        return load_manifest(manifest, verbose=verbose)
    else:
        default_manifest_locations = (
            path.with_suffix('.toml'),
            path.with_name(path.stem + '-gallery').with_suffix('.toml')
        )
        manifest = next((loc for loc in default_manifest_locations if loc.exists()), None)
        if manifest:
            return load_manifest(manifest, zola_path=False, verbose=verbose)

    return gallery

# Almost identical to the one in card.py but without the anchors
person_link_re = re.compile(r'''
    \[ # Square brackets surround link text
        (?: # Optional prefix
          (?P<delim>[*_]) # begins with an underscore or asterisk
          (?P<prefix>.*?) # followed by text
          (?P=delim) # ends with the same delimiter character
        )?
        \s* # May be followed by whitespace
        (?P<text>.*?)
        (?:\(c\))? # May have a champion marker, which we do not capture
        (?: # Optional suffix
          (?P<sdelim>[*_]) # begins with an underscore or asterisk
          (?P<suffix>.*?) # followed by text
          (?P=sdelim) # ends with the same delimiter character
        )?
    \]
    \( # Then, parentheses surround link target
        (?P<target>.*?)
    \)
    (?:\(c\))? # The champion marker may also be outside
    \s* # Eat whitespace
''', re.VERBOSE)

def parse_names(text):
    for mm in person_link_re.finditer(text):
        yield(mm.group('target'))

def combine_path(event_page: EventPage, subdir, photo_path: str) -> str:
    """Given an event page and a photo path that should be located in its directory, generate a path from content root."""
    # TODO: This should be an operation on contenttree? 
    content_root = Path.cwd() / 'content'
    relative = event_page.path.relative_to(content_root)
    slugified = Path(str(relative).replace('_', '-'))
    path = slugified / subdir / photo_path
    return str(path).replace('.md', '')

@singledispatch
def generate_key(page, index: int):
    return f"{page.path.stem}_{index}"

@generate_key.register
def generate_event_key(page: EventPage, index: int):
    """Given an event page and photo index, generate an identifier unique within that page."""
    ymd = page.event_date.strftime("%Y%m%d")
    return f"{ymd}_{index}"

def page_link(page: Page) -> str:
    content_root = Path.cwd() / 'content'
    path = page.path.relative_to(content_root)
    return f"[{page.title}](@/{path})"

def fix_caption(caption: str) -> str:
    """Tomllib loads long strings differently from zola."""
    return caption.replace("\n\n", "\n")

def build_event_photos(content, output_dir):
    all_photos = []
    photo_taggings = {}
    photo_index = 0

    for pageio in content.glob('content/e/**/????-??-??-*.md'):
        page = content.page(pageio)
        fm = page.front_matter
        gallery = load_gallery(fm, page.path, verbose=False)
        if not gallery: continue

        for _, entry in gallery.items():
            path, caption, source = entry['path'], entry['caption'], entry.get('source')
            if entry.get('skip_art', False):
                continue

            taggings = set(parse_names(caption))
            for page_path in taggings:
                entries = photo_taggings.setdefault(page_path.replace('@/', ''), [])
                entries.append(photo_index)

            key = generate_key(page, photo_index + 1)
            all_photos.append(
                (
                    key,
                    {
                        "caption": fix_caption(caption),
                        "source": source,
                        "path": f"/{combine_path(page, '', path)}",
                        "thumb": f"/{combine_path(page, 'tn', path)}",
                        "event": page_link(page)
                    }
                )
            )
            photo_index += 1

    save_as_json(all_photos, output_dir / 'all_photos.json')
    save_as_json(photo_taggings, output_dir / 'photo_taggings.json')

def build_other_photos(content, output_dir):
    other_photos = []
    photo_index = 0
    root = Path.cwd()

    def has_template(page, template):
        return page.front_matter and page.front_matter['template'] == template

    def load_pages(pageios):
        return (content.page(pageio) for pageio in pageios)

    all_talent_pages = load_pages(content.glob('content/e/**/????-??-??-*.md'))
    talent_pages = (doc for doc in all_talent_pages if has_template(doc, 'talent_page.html'))
    org_pages = (page for page in load_pages(content.glob('content/o/*.md')) if has_template(page, 'org_page.html'))
    venue_pages = (page for page in load_pages(content.glob('content/v/*.md')) if has_template(page, 'venue_page.html'))
    champ_pages = (page for page in load_pages(content.glob('content/c/*.md')) if page.front_matter)
    article_pages = (page for page in load_pages(content.glob('content/a/*.md')) if page.front_matter)
    all_pages = chain(talent_pages, org_pages, venue_pages, champ_pages, article_pages)

    for page in all_pages:
        gallery = load_gallery(page.front_matter, path=page.path, verbose=False)
        if not gallery: continue

        for _, entry in gallery.items():
            path, caption, source = entry['path'], entry['caption'], entry.get('source')
            if entry.get('skip_art', False):
                continue

            key = generate_key(page, photo_index + 1)
            info = {
                "caption": fix_caption(caption),
                "source": source,
                "path": f"/{combine_path(page, '', path)}",
                "thumb": f"/{combine_path(page, 'tn', path)}",
            }
            type_key = page_type_key(page)
            info[type_key] = page_link(page)

            other_photos.append((key, info))
            photo_index += 1

    save_as_json(other_photos, output_dir / 'talent_photos.json')

def save_as_json(data: Any, path: Path):
    with path.open('w') as fp:
        json.dump(data, fp)

def page_type_key(page: Page) -> str:
    match page:
        case TalentPage():
            return 'talent'
        case OrgPage(path=path) | Article(path=path) if path.match('o/*.md'):
            return 'org'
        case VenuePage(path=path) | Article(path=path) if path.match('v/*.md'):
            return 'venue'
        case Article(path=path) if path.match('c/*.md'):
            return 'championship'
        case Article(path=path) if path.match('a/*.md'):
            return 'article'
        case _:
            raise ValueError(f"Unknown page type for page {page!r}")

def process(content, output_dir):
    build_event_photos(content, output_dir)
    build_other_photos(content, output_dir)

if __name__ == "__main__":
    cwd = Path.cwd()
    parser = argparse.ArgumentParser(prog='build-metadata')
    parser.add_argument('-z', '--zipfile')
    args = parser.parse_args()
    if args.zipfile:
        content = ZipContentTree(Path(args.zipfile.strip()))
    else:
        content = FilesystemTree(cwd)

    output_dir = cwd / 'data'

    process(content, output_dir)
