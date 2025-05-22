from typing import Any

class Directive:
    @staticmethod
    def matches(row: list[Any]) -> bool:
        return row[0].startswith('@')

    def __init__(self, row: list[Any]):
        keyword, *params = row
        self.keyword = keyword
        self.params = params
