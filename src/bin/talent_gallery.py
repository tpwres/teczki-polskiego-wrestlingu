from typing import cast, Any, TypedDict, Optional
from page import all_event_pages, EventPage
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
    extra = cast(dict[str, Any], fm['extra'])
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

def combine_path(event_page: EventPage, photo_path: str):
    """Given an event page and a photo path that should be located in its directory, generate a path from content root."""
    content_root = Path.cwd() / 'content'
    relative = event_page.path.relative_to(content_root)
    return relative / photo_path

def main():
    all_photos = []
    photo_taggings = {}
    photo_index = 0

    for page in all_event_pages():
        fm = page.front_matter
        gallery = load_gallery(fm, verbose=False)
        if not gallery: continue

        for key, entry in gallery.items():
            path, caption, source = entry['path'], entry['caption'], entry.get('source')
            taggings = list(parse_names(caption))
            for page_path in taggings:
                entries = photo_taggings.setdefault(page_path.replace('@', ''), [])
                entries.append(photo_index)

            if taggings:
                # Skip photos that don't have anyone properly linked
                all_photos.append(
                    (
                        key,
                        {
                            "caption": caption,
                            "source": source,
                            "path": str(combine_path(page, path))
                        }
                    )
                )
                photo_index += 1

    save_as_json(all_photos, Path('data/all_photos.json'))
    save_as_json(photo_taggings, Path('data/photo_taggings.json'))

def save_as_json(data: Any, path: Path):
    with path.open('w') as fp:
        json.dump(data, fp)

if __name__ == "__main__":
    main()
