from .base import LintError, Changeset, Doc
from articles import load_event_articles
from dataclasses import dataclass
import re

@dataclass
class ReplaceEventTitleWithLink(Changeset):
    line_num: int
    start_col: int
    title: str
    link: str

    def apply_changes(self, doc: Doc):
        lines = []
        with doc.open('r') as fp:
            lines = fp.readlines()

        target_line = lines[self.line_num - 1]
        pat = re.compile(fr"(?!\[)({self.title})(?!\])")
        lines[self.line_num - 1] = pat.sub(self.link, target_line, count=1)

        with doc.open('w') as fp:
            fp.writelines(lines)

@dataclass
class UnlinkedEventError(LintError):
    path: Doc
    line_num: int
    start_col: int
    title: str
    link: str

    def supports_auto(self):
        return True

    def calculate_fix(self, body_text):
        return ReplaceEventTitleWithLink(self.line_num, self.start_col, self.title, self.link)

class UnlinkedEventLinter:
    def __init__(self):
        self.all_events = load_event_articles()
        event_titles = sorted(self.all_events.keys(), key=len, reverse=True)
        titles_union = '|'.join(re.escape(title) for title in event_titles)
        self.title_detection_regex = re.compile(fr"(?!\[)({titles_union})(?!\])")

    def lint(self, doc: Doc):
        with doc.open('r') as fp:
            errors = []
            for num, line in enumerate(fp.readlines()):
                self.find_matches(doc, line, num, errors)


            return errors

    def find_matches(self, doc, line, num, errors):
        for mm in self.title_detection_regex.finditer(line):
            title = mm.group(1)
            # TODO? test against link_regex

            article = self.all_events.get(title)
            if not article: continue

            parent = article.parent.name
            if parent == 'e':
                link = "[{}]@(/e/{})".format(title, article.name)
            else:
                link = "[{}](@/e/{}/{})".format(title, parent, article.name)
            errors.append(UnlinkedEventError(doc, num, mm.start(1), title, link))
