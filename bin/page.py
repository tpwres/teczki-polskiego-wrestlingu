import re
from datetime import datetime
from pathlib import Path
from card import Card
from utils import parse_front_matter

date_org_re = re.compile(r'^(?P<date>\d{4}-\d\d-\d\d)-(?P<orgs>[^-]+)')

class Page:
    def __init__(self, path: Path):
        print("Loading %s" % path)

        defaults = {}
        if m := date_org_re.match(path.stem):
            defaults['orgs'] = m.group('orgs').split('_')
            defaults['date'] = datetime.strptime(m.group('date'), '%Y-%m-%d').date()

        text = path.read_text(encoding='utf-8')
        front_matter = defaults | parse_front_matter(text)

        self.orgs = front_matter['orgs']
        self.event_date = front_matter['date']
        self.event_name = front_matter['title']

        # 3. Find and read the card() block
        self.card = Card(text)
