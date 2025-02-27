from typing import cast, Any, TypedDict, Optional
from functools import singledispatch
from page import all_event_pages, all_talent_pages, EventPage, TalentPage, Page
from pathlib import Path
import tomllib, re, json

class GalleryItem(TypedDict):
    path: str
    caption: str
    source: Optional[str]

def load_manifest(manifest_path, verbose = True) -> dict[str, GalleryItem]:
    """Given a manifest path, resolve it and load content as TOML."""
    content_path = Path.cwd() / 'content'
    resolved_path = Path(manifest_path.replace('@', str(content_path)))
    if verbose:
        print(f"Loading manifest from {resolved_path}")

    # Should support other formats, but TOML is the de-facto standard
    return tomllib.load(resolved_path.open('rb'))

def load_gallery(fm: dict[str, Any], verbose = True) -> Optional[dict[str, GalleryItem]]:
    """Load gallery from the provided front matter. Accepts galleries with manifests."""
    extra = cast(dict[str, Any], fm.get('extra', None))
    if not extra: return None

    gallery = cast(dict[str, GalleryItem], extra.get('gallery'))
    if not gallery: return None

    if (manifest := gallery.get('manifest')):
        return load_manifest(manifest, verbose=verbose)

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

def build_event_photos():
    all_photos = []
    photo_taggings = {}
    photo_index = 0

    for page in all_event_pages():
        fm = page.front_matter
        gallery = load_gallery(fm, verbose=False)
        if not gallery: continue

        for _, entry in gallery.items():
            path, caption, source = entry['path'], entry['caption'], entry.get('source')
            taggings = set(parse_names(caption))
            for page_path in taggings:
                entries = photo_taggings.setdefault(page_path.replace('@/', ''), [])
                entries.append(photo_index)

            if taggings:
                # Skip photos that don't have anyone properly linked
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

    save_as_json(all_photos, Path('data/all_photos.json'))
    save_as_json(photo_taggings, Path('data/photo_taggings.json'))

def build_people_photos():
    people_photos = []
    photo_index = 0

    for page in all_talent_pages():
        fm = page.front_matter
        if fm['template'] != 'talent_page.html':
            continue
        gallery = load_gallery(fm, verbose=False)
        if not gallery: continue

        for _, entry in gallery.items():
            path, caption, source = entry['path'], entry['caption'], entry.get('source')
            taggings = set(parse_names(caption))

            key = generate_key(page, photo_index + 1)
            people_photos.append(
                (
                    key,
                    {
                        "caption": fix_caption(caption),
                        "source": source,
                        "path": f"/{combine_path(page, '', path)}",
                        "thumb": f"/{combine_path(page, 'tn', path)}",
                        "talent": page_link(page)
                    }
                )
            )
            photo_index += 1

    save_as_json(people_photos, Path('data/talent_photos.json'))

def save_as_json(data: Any, path: Path):
    with path.open('w') as fp:
        json.dump(data, fp)

def main():
    build_event_photos()
    build_people_photos()

if __name__ == "__main__":
    main()
