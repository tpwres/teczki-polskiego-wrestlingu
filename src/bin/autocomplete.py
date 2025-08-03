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
from pathlib import Path
from typing import Dict, List

from parse.parser import RichDocParser

def build_autocomplete_cache(content_dir: Path) -> Dict[str, str]:
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
                autocomplete_map[name.lower()] = path

    # Scan different content directories
    for category in ['w', 'tt', 'v', 'c', 'o']:
        category_dir = content_dir / category
        if not category_dir.exists():
            continue

        for file_path in category_dir.glob('**/*.md'):
            # Parse file using RichDocParser
            doc = RichDocParser().parse_file(file_path)
            if not doc: continue

            name = doc.front_matter.get('title')
            autocomplete_map[name] = to_at_path(file_path)

    return autocomplete_map

def to_at_path(path, content_dir=Path.cwd() / 'content'):
    rel = path.relative_to(content_dir)
    return f"@/{rel}"

def save_autocomplete_cache(cache: Dict[str, str], cache_file: Path):
    """Save autocomplete cache as a compressed pickle"""
    with open(cache_file, 'wb') as f:
        compressed_cache = zlib.compress(pickle.dumps(cache))
        f.write(compressed_cache)

def load_autocomplete_cache(cache_file: Path, content_dir: Path) -> Dict[str, str]:
    """
    Load autocomplete cache, rebuilding if absent or stale
    Stale means cache is older than the newest markdown file
    """
    if not cache_file.exists():
        return build_autocomplete_cache(content_dir)

    # Check if cache is stale
    latest_md_time = max(
        (f.stat().st_mtime for f in content_dir.glob('**/*.md')),
        default=0
    )

    if cache_file.stat().st_mtime < latest_md_time:
        return build_autocomplete_cache(content_dir)

    # Load compressed cache
    with open(cache_file, 'rb') as f:
        return pickle.loads(zlib.decompress(f.read()))

def autocomplete(prefix: str, cache: Dict[str, str]) -> List[str]:
    """
    Find and format autocomplete matches for a given prefix
    """
    matches = sorted(
        (name for name, path in cache.items() if name.startswith(prefix)),
        key=lambda x: len(x)  # Shorter matches first
    )

    return [f"[{name}]({cache[name]})" for name in matches]

def main():
    """Main autocomplete script"""
    content_dir = Path.cwd() / 'content'
    cache_file = Path.cwd() / '.autocomplete_cache'

    # Load or build cache
    autocomplete_cache = load_autocomplete_cache(cache_file, content_dir)
    save_autocomplete_cache(autocomplete_cache, cache_file)

    # Read input prefix
    prefix = input().strip(' []')

    # Output matches
    print('\n'.join(autocomplete(prefix, autocomplete_cache)))

if __name__ == '__main__':
    main()
