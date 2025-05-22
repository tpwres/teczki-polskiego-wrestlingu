from datetime import datetime, timedelta
from itertools import repeat
import re
from typing import Optional

def parse_partial_date(text: str) -> datetime:
    "Parses a year-month or a year-month-date string into a datetime object."
    dashes = text.count('-')
    if dashes == 2:
        format = '%Y-%m-%d'
    elif dashes == 1:
        format = '%Y-%m'
    else:
        raise ValueError(f'Unsupported date {text} provided')

    return datetime.strptime(text, format)

class BandSpec:
    n: list[int]
    d: int

    def __init__(self, num: int|list[int], denom: int):
        match num:
            case int(num):
                self.n = [num]
            case [*nums]:
                self.n = nums
        self.d = denom

    @classmethod
    def parse(cls, band: str):
        if band == '':
            return cls(1, 1)
        # Accepts: a simple fraction like 1/3, and repeated bands like 1+3/3
        nums_list, _, denom = band.partition('/')
        nums = [int(part) for part in nums_list.split('+')]
        return cls(nums, int(denom))

    def __iter__(self):
        return zip(self.n, repeat(self.d))

class Stripe:
    name: str
    org: str
    start: datetime
    end: datetime
    duration: timedelta
    annotation: Optional[str]

    def __init__(self, row):
        name, org, start, end, *rest = row
        self.name, self.org = name, org
        self.start = parse_partial_date(start)
        self.end = datetime(2099,12,31) if end == '-' else parse_partial_date(end)

        # Adjust end date
        if end == '-':
            self.duration = datetime.today() - self.start
        else:
            self.duration = self.end - self.start

        self.annotation = None
        match rest:
            case [str(band), str(layer), str(annotation)]:
                self.layer = layer or '0'
                self.band = BandSpec.parse(band)
                self.annotation = annotation
            case [str(band), str(layer)]:
                self.layer = layer
                self.band = BandSpec.parse(band)
            case [str(band)]:
                self.layer = '0'
                self.band = BandSpec.parse(band)
            case []:
                self.layer = '0'
                self.band = BandSpec(1, 1)


    def overlaps(self, other_row):
        if self.start >= other_row.end:
            return False
        if self.end <= other_row.start:
            return False
        return True

    @property
    def all_orgs(self):
        match re.match(r'^(\w+)([|/\\])(\w+)$', self.org):
            case re.Match(group=group):
                return set([group(1), group(3)])
            case _:
                return set([self.org])

    def __repr__(self):
        return f"({self.name}@{self.org},{self.start}..{self.end},dur={self.duration},layer={self.layer},band={self.band})"
