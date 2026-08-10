#! /usr/bin/env python3

import sys
from pathlib import Path

def parse_input(stream):
    mtime: dict[str, str] = {}
    date: str|None = None
    for raw in stream:
        line = raw.rstrip("\n")
        match line.split(maxsplit=1):
            case [""]:
                continue
            case ["D", d]:
                date = d
                continue
            case [path]:
                if not path.endswith(".md") or path.endswith("_index.md"):
                    continue
                if not date or path in mtime:
                    continue
                if not Path(path).is_file():
                    continue # Checks if not deleted
                mtime[path] = date
    return mtime

def main(stream):
    mtime = parse_input(stream)

    for path, updated in mtime.items():
        p = Path(path)
        lines = p.read_text().splitlines(keepends=True)

        for i, ln in enumerate(lines):
            if ln.strip() == "+++": # Immediately after frontmatter delimiter
                lines.insert(i+1, f"""updated = "{updated}"\n""")
                break

        p.write_text("".join(lines))

if __name__ == "__main__":
    if len(sys.argv) > 1:
        _, path = sys.argv
        main(open(path))
    else:
        main(sys.stdin)
