from yaml import tokens as t
from enum import Enum, auto

class CardState(Enum):
    Empty = auto()
    MatchList = auto()
    MatchLine = auto()
    MatchOptions = auto()
    OptionKey = auto()
    OptionValue = auto()
    SpecialRow = auto()
    SpecialRowKey = auto()
    SpecialRowValue = auto()
    CrewEntry = auto()
    CrewKey = auto()
    CrewValue = auto()

S = CardState

# NOTE: not reusable, create a new CardStateMachine after iterating
class CardStateMachine:
    def __init__(self, tokens: list[t.Token], /, **handlers):
        self.tokens = tokens
        self.handlers = handlers

    def __iter__(self):
        self.state = CardState.Empty
        self.iter_tokens = iter(self.tokens)
        return self

    def __next__(self):
        token = next(self.iter_tokens)
        new_state, replacement_token = self.advance_state(token, self.state)
        self.state = new_state
        return (token, replacement_token)

    def handle(self, key, token, *args):
        # print(f"H({key}, {token}, {args})")
        if key in self.handlers:
            return self.handlers[key](token, *args)

    def advance_state(self, token, state):
        replacement = None
        match (state, token):
            case (S.Empty, t.BlockSequenceStartToken()):
                state = S.MatchList
            case (S.MatchList, t.BlockEndToken()):
                state = S.Empty
            case (S.MatchList, t.BlockSequenceStartToken() | t.FlowSequenceStartToken()):
                state = S.MatchLine
            case (S.MatchLine | S.MatchOptions, token):
                state, replacement = self.advance_matchline_state(token, state)
            case (S.OptionKey | S.OptionValue, token):
                state, replacement = self.advance_options_state(token, state)
            case (S.MatchList, t.BlockMappingStartToken()):
                # credits row or delimiter
                state = S.SpecialRow
            case (S.SpecialRow, t.KeyToken()):
                state = S.SpecialRowKey
            case (S.SpecialRow, t.ValueToken()):
                state = S.SpecialRowValue
            case (S.SpecialRowKey | S.SpecialRowValue, token):
                state, replacement = self.advance_sr_state(token, state)
            case (S.CrewEntry | S.CrewKey | S.CrewValue, token):
                state, replacement = self.advance_crew_state(token, state)
            case (S.SpecialRow, t.BlockEndToken()):
                state = S.MatchList
            case (_, t.StreamStartToken() | t.StreamEndToken()):
                pass
            case (_, t.BlockEntryToken()): # another element in a list or mapping
                pass

        return state, replacement

    def advance_matchline_state(self, token, state):
        replacement = None
        match (state, token):
            case (S.MatchLine, t.BlockEndToken()):
                state = S.MatchList
            case (S.MatchLine, t.ScalarToken(value=value)):
                # This is a single opponent or team
                replacement = self.handle('match_opponent', token, value)
            case (S.MatchLine, t.BlockMappingStartToken() | t.FlowMappingStartToken()):
                state = S.MatchOptions
            case (S.MatchOptions, t.BlockEndToken()):
                state = S.MatchLine
            case (S.MatchOptions, t.KeyToken()):
                state = S.OptionKey
            case (S.MatchOptions, t.ValueToken()):
                state = S.OptionValue

        return state, replacement

    def advance_options_state(self, token, state):
        replacement = None
        match (state, token):
            case (S.OptionKey, t.ScalarToken(value=value)):
                self.option_key = value
                state = S.MatchOptions
            case (S.OptionValue, t.ScalarToken(value=value)):
                replacement = self.handle('option_value', token, self.option_key, value)
                self.option_key = None
                state = S.MatchOptions

        return state, replacement

    def advance_sr_state(self, token, state):
        replacement = None
        match (state, token):
            case (S.SpecialRowKey, t.ScalarToken(value=value)):
                self.special_row_key = value
                state = S.SpecialRow
            case (S.SpecialRowValue, t.ScalarToken(value=value)):
                replacement = self.handle('special_option_value', token, self.special_row_key, value)
                self.special_row_key = None
                state = S.SpecialRow
            case (S.SpecialRowValue, t.BlockMappingStartToken()):
                # crew entry
                state = S.CrewEntry
            case _:
                breakpoint()

        return state, replacement

    def advance_crew_state(self, token, state):
        replacement = None
        match (state, token):
            case (S.CrewEntry, t.BlockEndToken()):
                state = S.SpecialRow
            case (S.CrewEntry, t.KeyToken()):
                state = S.CrewKey
            case (S.CrewKey, t.ScalarToken(value=value)):
                self.crew_key = value
                state = S.CrewEntry
            case (S.CrewEntry, t.ValueToken()):
                state = S.CrewValue
            case (S.CrewValue, t.ScalarToken(value=value)):
                replacement = self.handle('crew_entry', token, self.crew_key, value)
                self.crew_key = None
                state = S.CrewEntry
            case _:
                breakpoint()

        return state, replacement
