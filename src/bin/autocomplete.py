# Autocomplete first tries to load its cached data, and only builds it if it's absent, or stale
# Stale means that the cache file is older than the newest *.md file in content/
# The cache file is essentially a dict, mapping a name to a path
# For talent, all applicable names should map to the talent's article. These can be read from the articles under content/w frontmatter, and from the data/aliases.json file
# For teams, this mapping can be read from the frontmatter of all files under content/tt
# For venues, similarly reading frontmatter of all files under content/v
# For championships, similarly reading frontmatter of all files under content/c
# This mapping is then saved, in a format that is quick to load - for example, a zlib-compressed pickle
# Reading files should be done with the RichDoc parser.

# Upon invoking, autocomplete reads stdin up to the first newline or eof
# The text read is used as prefix, and searched in the mapping
# All entries that match the prefix are retrieved, sorted lexicographically and printed to stdout, but formatted as links
# For example, if we have Gordon: /w/gordon.md, Gotham: /v/gotham.md, and Gotham City Police Dept: /tt/gotham-police.md,
# then a search for `go` should produce, in that order [Gordon](@/w/gordon.md), [Gotham](@/v/gotham.md), [Gotham City Police Dept](/tt/gotham-police.md)
import json
import pickle
import zlib
import sys
from pathlib import Path
from typing import List, Any, Optional
from dataclasses import dataclass, asdict, is_dataclass
from functools import cache
from argparse import ArgumentParser

from parse.parser import RichDocParser

@dataclass
class CompletionItem:
    path: str
    cat: str # Category
    rel: Optional[str] = None

@cache
def get_title(path: Path) -> str:
    doc = RichDocParser().parse_file(path)
    return doc.front_matter.get('title')

def build_autocomplete_cache(content_dir: Path) -> dict[str, str]:
    """
    Build a mapping of names to paths for autocomplete functionality.
    Reads frontmatter from markdown files in various subdirectories.
    """
    autocomplete_map = {}

    # Load aliases from data/aliases.json
    aliases_path = content_dir.parent / 'data' / 'aliases.json'
    if aliases_path.exists():
        with open(aliases_path, 'r') as f:
            aliases = json.load(f)
            for name, path in aliases.items():
                original = get_title(content_dir / path)
                autocomplete_map[name] = CompletionItem(path, 'a', original)

    # Scan different content directories
    for category in ['w', 'tt', 'v', 'c', 'o', 'e']:
        category_dir = content_dir / category
        if not category_dir.exists():
            continue

        for file_path in category_dir.glob('**/*.md'):
            name = get_title(file_path)
            autocomplete_map[name] = CompletionItem(
                to_at_path(file_path),
                category
            )

    return autocomplete_map

def to_at_path(path, content_dir=Path.cwd() / 'content'):
    rel = path.relative_to(content_dir)
    return f"@/{rel}"

def save_autocomplete_cache(cache: dict[str, str], cache_file: Path):
    """Save autocomplete cache as a compressed pickle"""
    with open(cache_file, 'wb') as f:
        compressed_cache = zlib.compress(pickle.dumps(cache))
        f.write(compressed_cache)

def load_autocomplete_cache(cache_file: Path, content_dir: Path) -> tuple[bool, dict[str, str]]:
    """
    Load autocomplete cache, rebuilding if absent or stale
    Stale means cache is older than the newest markdown file
    """
    if not cache_file.exists():
        return True, build_autocomplete_cache(content_dir)

    # Check if cache is stale
    latest_md_time = max(
        (f.stat().st_mtime for f in content_dir.glob('**/*.md')),
        default=0
    )

    if cache_file.stat().st_mtime < latest_md_time:
        return True, build_autocomplete_cache(content_dir)

    # Load compressed cache
    with open(cache_file, 'rb') as f:
        return False, pickle.loads(zlib.decompress(f.read()))

def autocomplete(prefix: str, cache: dict[str, str]) -> List[str]:
    """
    Find and format autocomplete matches for a given prefix
    """
    lower_prefix = prefix.lower()
    matches = sorted(
        ((name, entry) for name, entry in cache.items() if name.lower().startswith(lower_prefix)),
        key=lambda n: len(n[0])  # Shorter matches first
    )

    return matches

def encode_item(item: Any):
    match item:
        case dc if is_dataclass(dc):
            return asdict(dc)
        case value:
            return value

def format_link(item):
    match item:
        case (str(name), CompletionItem(path=path)):
            return f"[{name}]({path})"

def main(options):
    """Main autocomplete script"""
    content_dir = Path.cwd() / 'content'
    cache_file = Path.cwd() / '.autocomplete_cache'

    # Load or build cache
    stale, autocomplete_cache = load_autocomplete_cache(cache_file, content_dir)
    if stale:
        save_autocomplete_cache(autocomplete_cache, cache_file)

    # Read input prefix
    prefix = input().strip(' []')
    matches = autocomplete(prefix, autocomplete_cache)

    # Output matches
    if options.json:
        json.dump(matches, sys.stdout, default=encode_item)
    else:
        print('\n'.join(format_link(entry) for entry in matches))

if __name__ == '__main__':
    parser = ArgumentParser(prog=sys.argv[0], description='Autocomplete markdown links')
    parser.add_argument('--json', action='store_true', help='Output JSON')
    options = parser.parse_args()
    main(options)
