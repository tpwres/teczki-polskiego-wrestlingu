import re
import json
from collections import defaultdict
from pathlib import Path
from linters.base import LintError, Doc, Linter
from linters.errors import FileError, FileWarning, LintWarning, ConsoleErrorSink, format_error
from card import person_link_re, person_plain_re
from rich_doc import RichDoc, FreeCardBlock
from md_utils import parse_link

F = FileError
W = FileWarning

class ChampionshipUpdatedLinter(Linter):
    """
    A well formed championship file has:
    - zero or more free_card blocks, each of which
      - contains valid, non-empty yaml
      - each entry is a match row with at least one participant
        - has an option block with required keywords en, ed
        - if en is a markdown link, it points to an existing file
        - the match can be found in that file's card
        - participants and options other than en, ed MUST be the same as in the match line in event file
    """
    def __init__(self, config, linter_options, error_sink=None):
        self.messages = []
        self.sink = error_sink or ConsoleErrorSink()
        self.load_required_metadata()

    def handles(self, path: Path) -> bool:
        return path.stem != '_index' and path.match('content/c/*.md')

    def reset(self):
        pass

    def load_required_metadata(self):
        all_matches_path = Path.cwd() / 'data/all_matches.json'
        self.all_matches = json.load(all_matches_path.open('rb'))

    def error(self, message, *args):
        self.sink.error(format_error(message, self.target_path, *args))

    def warning(self, message, *args):
        self.sink.warning(format_error(message, self.target_path, *args))

    def lint(self, document: Doc):
        path = document.pathname()
        try:
            self.content_root = [p for p in path.parents if p.stem == 'content'].pop()
        except IndexError:
            self.content_root = Path.cwd() / 'content'

        self.target_path = path

        rd = RichDoc.from_file(path, error_sink=self.sink)
        self.championship_name = rd.title
        fc_blocks = [(start_line, block)
                     for start_line, _name, block in rd.sections
                     if isinstance(block, FreeCardBlock)]
        self.validate_blocks(fc_blocks)


        return self.messages

    def validate_blocks(self, blocks):
        for i, (starting_line, block) in enumerate(blocks, start=1):
            location = f'free card block {i}'
            if not block:
                self.error(f'{location} is blank')

            fc = block.raw_card
            if fc is None:
                self.error(f'{location} is empty or invalid', starting_line, None)
                return

            if not isinstance(fc, list):
                self.error(f"{location} does not parse as a list", starting_line, None)
            else:
                self.validate_match_block(fc, location, starting_line)

    def validate_match_block(self, matchlines, location, starting_line):
        for i, matchline in enumerate(matchlines, start=1):
            opts = matchline.pop()
            if not isinstance(opts, dict):
                self.error(f"required option block for match {i} in {location} missing", starting_line, None)
                continue

            en, ed = opts.get('en'), opts.get('ed')
            if not en:
                self.error(f"Match {i} in {location} is missing an `en` entry", starting_line, None)

            if not ed:
                self.error(f"Match {i} in {location} is missing an `ed` entry", starting_line, None)

            if en and '](' in en:
                prefix = f'In {location}'
                self.validate_event_file(en, ed, prefix, starting_line)

                self.validate_match_in_card([*matchline, opts], prefix, starting_line)

    def validate_event_file(self, event_link, event_date, prefix, starting_line):
        title, event_path = parse_link(event_link)
        event_path = event_path.replace('@', str(self.content_root)) # Convert from @-path
        path = Path(event_path)

        if not path.match(f'{event_date}-*.md'):
            self.warning(f"{prefix} date mismatch `{event_date}` does not match its filename {str(path)}", starting_line, None)
        if not path.exists():
            self.error(f"{prefix} invalid link to non-existent event file `{event_link}`", starting_line, None)
            return

        # NOTE: Could be cached
        doc = RichDoc.from_file(path, error_sink=self.sink)
        fm_title = doc.front_matter.get('title')

        # Accept partial name (e.g. KPW Godzina Zero 2024 vs Godzina Zero 2024 is ok)
        if title not in fm_title:
            self.warning(f"{prefix} title mismatch `{title}` does not match title `{fm_title}` from {str(path)}", starting_line, None)

    def validate_match_in_card(self, fight, prefix, starting_line):
        opts = fight.pop()
        en = opts.pop('en')

        _title, event_path = parse_link(en)
        full_path = event_path.replace('@', str(self.content_root)) # Convert from @-path
        path = Path(full_path)
        if not path.exists():
            return

        rel_path = event_path.replace('@/', '')
        # All bouts at this event
        bouts = [m for m in self.all_matches if m['p'] == rel_path]
        championship_matches = self.find_relevant_match(bouts, participants=fight, opts=opts, prefix=prefix, event_path=rel_path)
        if championship_matches is None:
            return

        if not championship_matches:
            self.error(f'{prefix} relevant match not found in event card at {rel_path}, participants may be different', starting_line, None)
        num_matches = len(championship_matches)

        # TODO: Extract this bit
        cm_errors = defaultdict(lambda: [])
        cm_warnings = defaultdict(lambda: [])
        for i, cm in enumerate(championship_matches):
            *_teams, cm_opts = cm['m']
            stip, card_stip = opts.get('s'), cm_opts.get('s')
            # TODO: stip_compatible() method
            if stip and stip != card_stip and not (card_stip is None and stip == 'Singles match'):
                cm_warnings[i].append(f"{prefix} stipulation mismatch: `{stip}` in article, `{card_stip}` in card")
            nc, card_nc = opts.get('nc'), cm_opts.get('nc')
            if nc and nc != card_nc:
                cm_errors[i].append(f"{prefix} ruling (nc) mismatch: `{nc}` in article, `{card_nc}` in card")

            result, card_result = opts.get('r'), cm_opts.get('r')
            if result and result != card_result:
                cm_warnings[i].append(f"{prefix} result mismatch: `{result}` in article, `{card_result}` in card")

        if len(cm_errors) < num_matches and len(cm_warnings) < num_matches:
            # If at least one matched on title + participants, and flags r(esult), s(tipulation) and nc(no-contest), we're good
            return

        for _, errs in cm_errors.items():
            for err in errs: self.error(err, starting_line, None)

        for _, warns in cm_warnings.items():
            for warn in warns: self.warning(warn, starting_line, None)

    def find_relevant_match(self, bouts, participants, opts, prefix, event_path):
        participants = list(only_names(participants))
        championship_matches = [bout
                                for bout in bouts
                                if (matchline := bout['m'])
                                and isinstance(opts := matchline[-1], dict)
                                and self.championship_name in opts.get('c', '')]
        if not championship_matches:
            self.error(f'{prefix} championship match not found in event card at {event_path}')
            return None

        # Could be more than one at this point. Now find one with the same participants
        same_participant_matches = [bout
                                    for bout in championship_matches
                                    if (matchline := bout['m'])
                                    and (opponents := matchline[:-1])
                                    and all(any(p in opp for opp in opponents) for p in participants)]

        # Still could be more than one, maybe an instant rematch or restart
        return same_participant_matches

def only_names(participants):
    for pp in participants:
        if mm := person_link_re.match(pp):
            yield mm['text'].strip()
        elif mm := person_plain_re.match(pp):
            yield mm['text'].strip()
