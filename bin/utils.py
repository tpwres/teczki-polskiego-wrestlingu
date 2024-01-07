import tomllib
from json import JSONEncoder
from collections import Counter

def extract_front_matter(text):
    matter = []
    lines = iter(text.split("\n"))
    while True:
        line = next(lines)
        if line == "+++": break

    while True:
        line = next(lines)
        if line == "+++": break
        matter.append(line)

    return "\n".join(matter)

def parse_front_matter(text):
    return tomllib.loads(extract_front_matter(text))

class RichEncoder(JSONEncoder):
    def default(self, obj):
        match obj:
            case set():
                return list(obj)
            case Counter():
                return dict(obj)
            case _:
                return super().default(obj)
