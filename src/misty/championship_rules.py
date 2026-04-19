from typing import List, Optional, Tuple, Dict, Any, TextIO
from pathlib import Path
import re
from dataclasses import dataclass
from misty.dsl import Rule, SingleMatch, Token, Message, Level, Fixable
from misty import emit_tokens_with_lines

@dataclass
class ChampionInfo:
    name: str
    is_vacant: bool
    is_tag_team: bool
    members: List[str]  # For tag teams
    source_event: str
    source_date: str

class ChampionshipSynchronization(Rule):
    """
    Validates that championship information in organization files
    matches the current champion data in championship articles.
    """
    pattern = SingleMatch(type='ZolaLink')

    # Cache for parsed championship data to avoid re-reading files
    _championship_cache: Dict[str, ChampionInfo] = {}

    def __init__(self):
        self.content_root = Path('content')

    def matches_championship_link(self, _type, _pos, args) -> bool:
        """Check if this ZolaLink points to a championship article."""
        target, text = args
        # Check if it's a link to a championship in content/c/
        return (target.startswith('@/c/') and
                'championship' in target.lower() and
                target.endswith('.md'))

    def process(self, token: Token) -> Optional[Token]:
        """Auto-fix championship references if possible."""
        # For now, we'll just validate, not auto-fix
        return None

    def describe(self, token: Token) -> Optional[List[Message]]:
        """Validate championship information and report discrepancies."""
        token_type, (row, col), args = token

        if not self.matches_championship_link(token_type, (row, col), args):
            return None

        # Get the actual championship info from the article
        champ_info = self.get_championship_info(args[0])
        if champ_info is None:
            return [Message(
                text=f"Could not read championship article: {args[0]}",
                location=(row, col),
                level=Level.ERROR
            )]

        # Now we need to find what the org file claims is the current champion
        # This requires parsing the context around the championship link
        # For now, we'll just validate that the championship article exists
        # and report its current champion

        messages = []

        if champ_info.is_vacant:
            messages.append(Message(
                text=f"{args[1]} is currently VACANT (last held by {champ_info.name})",
                location=(row, col),
                level=Level.INFO
            ))
        elif champ_info.is_tag_team:
            members_str = " & ".join(champ_info.members)
            messages.append(Message(
                text=f"{args[1]} current champions: {members_str}",
                location=(row, col),
                level=Level.INFO
            ))
        else:
            messages.append(Message(
                text=f"{args[1]} current champion: {champ_info.name}",
                location=(row, col),
                level=Level.INFO
            ))

        return messages

    def get_championship_info(self, target: str) -> Optional[ChampionInfo]:
        """Parse a championship article to extract current champion information."""
        # Convert target path to filesystem path
        if target.startswith('@/'):
            fs_path = self.content_root / target[2:]
        else:
            fs_path = self.content_root / target

        # Check cache first
        if str(fs_path) in self._championship_cache:
            return self._championship_cache[str(fs_path)]

        try:
            with open(fs_path, 'r', encoding='utf-8') as f:
                # Parse the championship article using misty parser
                champ_info = self.parse_championship_article_with_misty(f, fs_path)
        except (FileNotFoundError, UnicodeDecodeError):
            return None

        # Cache the result
        if champ_info:
            self._championship_cache[str(fs_path)] = champ_info

        return champ_info

    def extract_free_card_blocks(self, tokens: List[Token]) -> List[List[Token]]:
        """Extract all free_card blocks from a list of tokens."""
        free_card_blocks = []
        current_block = None
        
        for token in tokens:
            match token:
                case ('ContentBlockStart', _, ('free_card',)):
                    # Start collecting tokens for this free_card block
                    current_block = []
                case ('ContentBlockEnd', _, _) if current_block is not None:
                    # End of free_card block, save it
                    free_card_blocks.append(current_block)
                    current_block = None
                case _ if current_block is not None:
                    # We're inside a free_card block, collect this token
                    current_block.append(token)
        
        return free_card_blocks

    def parse_championship_article_with_misty(self, file_stream: TextIO, file_path: Path) -> Optional[ChampionInfo]:
        """Parse championship article content using misty parser to find current champion."""
        try:
            tokens = list(emit_tokens_with_lines(file_stream))
        except Exception:
            # If parsing fails, return None
            return None
        
        # Find all free_card blocks in the article
        free_card_blocks = self.extract_free_card_blocks(tokens)
        
        if not free_card_blocks:
            return None
        
        # Get the last free_card block
        last_free_card_tokens = free_card_blocks[-1]
        
        # Parse the free_card tokens to find the last match entry
        current_champion_match = None
        for token in last_free_card_tokens:
            match token:
                case ('Text', _, (text,)) if text.startswith('- - '):
                    # This is a match entry
                    current_champion_match = text[4:]  # Remove '- - '
                case ('Text', _, (text,)) if 'TOTAL:' in text:
                    # End of championship reign
                    break
        
        if not current_champion_match:
            return None
        
        # Parse the match entry to find the champion(s)
        return self.parse_match_entry(current_champion_match, file_path)

    def parse_match_entry(self, match_entry: str, file_path: Path) -> Optional[ChampionInfo]:
        """Parse a single match entry to extract champion information."""
        # Split by ' - ' to get participants
        participants = [p.strip() for p in match_entry.split(' - ')]

        # Check if this is a vacated title match
        vacated_keywords = ['vacant', 'vacated', 'stripped', 'retired']
        for keyword in vacated_keywords:
            if keyword in match_entry.lower():
                # Find who the last champion was before vacancy
                # Look for the previous match entry
                return ChampionInfo(
                    name="Vacant",
                    is_vacant=True,
                    is_tag_team=False,
                    members=[],
                    source_event="Vacated",
                    source_date=""
                )

        # Extract wrestler names from the match entry
        wrestlers = []
        for participant in participants:
            # Look for wrestler links: [Name](@/w/name.md)
            wrestler_matches = re.findall(r'\[([^\]]+)\]\(@/w/[^)]+\)', participant)
            wrestlers.extend(wrestler_matches)

        if not wrestlers:
            return None

        # Determine if this is a tag team championship
        is_tag_team = len(wrestlers) > 1

        # Extract event information if available
        event_info = ""
        date_info = ""

        # Look for event and date in the remaining content
        if 'en:' in match_entry:
            event_match = re.search(r"en:\s*'\[([^\]]+)\]'", match_entry)
            if event_match:
                event_info = event_match.group(1)

        if 'ed:' in match_entry:
            date_match = re.search(r"ed:\s*(\d{4}-\d{2}-\d{2})", match_entry)
            if date_match:
                date_info = date_match.group(1)

        # For tag teams, the champion is the team
        if is_tag_team:
            champion_name = f"{' & '.join(wrestlers)}"
        else:
            champion_name = wrestlers[0]

        return ChampionInfo(
            name=champion_name,
            is_vacant=False,
            is_tag_team=is_tag_team,
            members=wrestlers,
            source_event=event_info,
            source_date=date_info
        )

class OrganizationChampionshipValidator(Rule):
    """
    Extended rule that validates championship blocks in organization files.
    This looks for specific patterns like the championship() liquid block.
    """
    pattern = SingleMatch(type='=championship')

    def process(self, token: Token) -> Optional[List[Token]]:
        """Auto-fix championship liquid blocks if possible."""
        # For now, just return None to keep the original token
        return None

    def describe(self, token: Token) -> Optional[List[Message]]:
        """Validate championship liquid blocks."""
        token_type, (row, col), args = token

        # Parse championship block arguments
        if not args:
            return [Message(
                text="championship() block requires arguments",
                location=(row, col),
                level=Level.ERROR
            )]

        # The args should contain championship information
        # For now, just validate the syntax
        messages = []

        try:
            # Simple syntax validation
            if not isinstance(args, str):
                messages.append(Message(
                    text=f"championship() expects string arguments, got {type(args)}",
                    location=(row, col),
                    level=Level.ERROR
                ))
        except Exception as e:
            messages.append(Message(
                text=f"Error parsing championship() block: {e}",
                location=(row, col),
                level=Level.ERROR
            ))

        return messages

# Add to default rules
extended_rules = [
    ChampionshipSynchronization,
    OrganizationChampionshipValidator,
]
