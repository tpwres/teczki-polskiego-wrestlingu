from typing import Iterable, Tuple
from dataclasses import dataclass
from .base import LintError, Changeset, Doc
from card import Card
from articles import load_existing_name_articles
from sys import exit
import re

@dataclass
class ReplaceNameWithLink(Changeset):
    line_num: int
    start_col: int
    name: str
    link: str

    def apply_changes(self, path: Doc):
        lines = []
        with path.open('r') as fp:
            lines = fp.readlines()

        hot_line = lines[self.line_num - 1] # 1-based
        pat = re.compile(fr"(?!\[)({self.name})(?!\])")
        lines[self.line_num - 1] = pat.sub(self.link, hot_line, count=1)

        with path.open('w') as fp:
            fp.writelines(lines)

@dataclass
class UnlinkedNameError(LintError):
    path: Doc
    line_num: int
    start_col: int
    name: str
    link: str

    def __str__(self):
        return "Line {} column {}: replace {} with link {}".format(self.line_num, self.start_col, self.name, self.link)

    def message(self, file_root: Doc):
        return "[{}] {}".format(self.path.relative_to(file_root), self)

    def supports_auto(self):
        return True

    def calculate_fix(self, body_text):
        return ReplaceNameWithLink(self.line_num, self.start_col, self.name, self.link)


class UnlinkedNameLinter:
    def __init__(self, config):
        self.names_with_articles = load_existing_name_articles()
        all_names = sorted(self.names_with_articles.keys(), key=len, reverse=True)
        name_union = '|'.join(re.escape(name) for name in all_names)
        self.name_detector_regex = re.compile(fr"(?!\[)({name_union})(?!\])")

    def lint(self, path: Doc):
        with path.open('r') as fp:
            errors = []
            flagged_names = set([])
            for num, line in self.skip_front_matter_and_card(fp.readlines()):
                for m in self.name_detector_regex.finditer(line):
                    name = m.group(1)
                    if name in flagged_names:
                        continue # Only flag a name once per file
                    if self.link_regex(name).search(line):
                        continue # Only replace if a line does not already hold a link for this person
                    flagged_names.add(name)

                    article = self.names_with_articles.get(name)
                    if not article: continue

                    if path.match(article.name):
                        # Don't add links to self when linting talent articles
                        continue

                    link = "[{}](@/w/{})".format(name, article.name)
                    errors.append(UnlinkedNameError(path, num, m.start(1), name, link))

            return errors

    def link_regex(self, name: str) -> re.Pattern:
        return re.compile(fr'\[{name}\]')

    def skip_front_matter_and_card(self, lines: list[str]) -> Iterable[Tuple[int, str]]:
        """Return an enumeration of lines in the file, starting from 1.
        However, skips the front matter and the card block, if any.
        """
        front_matter = False
        card = False
        for num, line in enumerate(lines, start=1):
            text = line.strip()
            if text == '+++':
                front_matter = not front_matter

            if front_matter:
                continue

            if not card and text == '{% card() %}':
                card = True
            if card and text == '{% end %}':
                card = False
                continue

            if not card:
                yield (num, line)

