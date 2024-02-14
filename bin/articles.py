from pathlib import Path
from utils import parse_front_matter

def load_existing_name_articles() -> dict[str, Path]:
    cwd = Path.cwd()
    talent_dir = cwd / 'content/w'
    name_files = talent_dir.glob('*.md')
    names = {}
    for path in name_files:
        if path.name == '_index.md': continue
        with path.open('r') as fp:
            text = fp.read()
            front_matter = parse_front_matter(text)
            names[front_matter['title']] = path
            if extra := front_matter.get('extra'):
                for alias in extra.get('career_aliases', []):
                    names[alias] = path

    return names

def load_names_with_aliases() -> dict[str, set[str]]:
    cwd = Path.cwd()
    talent_dir = cwd / 'content/w'
    name_files = talent_dir.glob('*.md')
    names = {}
    for path in name_files:
        if path.name == '_index.md': continue
        with path.open('r') as fp:
            text = fp.read()
            front_matter = parse_front_matter(text)
            extra = front_matter.get('extra', {})
            title = front_matter['title']

            preferred_name = extra.get('career_name', title)
            names[preferred_name] = set([])
            aliases = extra.get('career_aliases', [])
            names[preferred_name] |= set(aliases)

    return names
