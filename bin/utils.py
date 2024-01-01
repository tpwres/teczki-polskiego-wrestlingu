import tomllib
from json import JSONEncoder
from collections import Counter
import yaml
from io import StringIO
import re

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


def extract_card_block(text):
    card = []
    lines = iter(text.split("\n"))
    for line in lines:
        if line == "{% card() %}": break
    else:
        # Start code not found
        return None

    for line in lines:
        if line == "{% end %}": break
        card.append(line)
    else:
        # End block code not found
        return None

    return "\n".join(card)

def parse_card_block(card):
    text = extract_card_block(card)
    data = yaml.safe_load(StringIO(text))
    return data

def extract_names(card):
    # Card is a list of lists
    # The inner lists name participants, and the last element may be a hash of extra data, which we skip
    all_names = []
    for row in card:
        entries = row[:]
        if isinstance(entries[-1], dict):
            entries.pop()
        for entry in entries:
            all_names.extend(find_names(entry))
    return all_names

# An entry may contain more than one name
# Either as plain names, [Linked Names](@/w/someone.md)
# or Tag Team Name: ...names
# Names are separated by plus (+) signs
def find_names(entry):
    tag_team_re = re.compile('^(?:([\w\s]+):)?\s*(.+)$')
    partners = [n.strip() for n in entry.split("+")]
    all_names = []
    for maybe_team in partners:
        m = tag_team_re.match(maybe_team)
        names = re.split(r'\s*,\s*', m.group(2))
        all_names.extend(names)
    return all_names

markdown_link_re = re.compile(r'^\[(.*?)(?:\(c\))?\]\(.*\)(?:\(c\))?$')
