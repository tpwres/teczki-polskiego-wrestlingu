from yaml import tokens, events
from yaml._yaml import CParser, CEmitter
from io import StringIO
import pdb

class Rewriter:
    """
    Parses YAML at a token level, and outputs it back.
    If replacement patterns are defined, scalar tokens will have their text replaced with these
    patterns, which are just string pairs for now.
    """
    def __init__(self, text: str):
        self.stream = StringIO(text)
        self.patterns = {}

    def add_replacement(self, token_value, replacement_value):
        self.patterns[token_value] = replacement_value

    def replace_in_scalar(self, scalar_value: str) -> str:
        new_value = scalar_value
        for pat, repl in self.patterns.items():
            new_value = new_value.replace(pat, repl)
        return new_value

    QUOTES = "'\""
    def rewrite(self):
        """
        Edits a YAML stream token by token.
        Handles enough YAML to parse the card blocks, which is just block and flow lists,
        and maps. Cannot output an implicit map yet, i.e. without delimiting braces.
        """
        parser = CParser(self.stream)
        out = StringIO()

        # Default is to not allow unicode, and replace non-ascii with \uxxxx escapes
        emitter = CEmitter(out, allow_unicode=True)

        # A document must begin with these
        emitter.emit(events.StreamStartEvent(encoding=None))
        emitter.emit(events.DocumentStartEvent())

        # A stack of currently open sequences.
        seqs = []
        indices = []

        while True:
            token = parser.get_token()
            # print("T={} S={!r} I={!r}".format(token, seqs, indices))

            match token:
                # A stream starts with this
                case tokens.StreamStartToken(encoding=encoding):
                    pass
                # A scalar can be a list entry, a mapping key or value.
                # Output it as closely to the original as possible, but replace text in value
                # according to defined patterns
                case tokens.ScalarToken(plain=plain, style=style, value=value, start_mark=start, end_mark=end_) as scalar:
                    new_value = self.replace_in_scalar(value)
                    emitter.emit(events.ScalarEvent(anchor=None,
                                                    tag=None,
                                                    # Try to preserve plain tokens
                                                    implicit=(plain, style in Rewriter.QUOTES),
                                                    style=style,
                                                    start_mark=start,
                                                    end_mark=end_,
                                                    value=new_value))
                # The next two tokens start a sequence, either flow or block style.
                case tokens.BlockSequenceStartToken(start_mark=start, end_mark=endm):
                    emitter.emit(events.SequenceStartEvent(
                        anchor=None,
                        tag=None,
                        implicit=1,
                        start_mark=start,
                        end_mark=endm,
                        flow_style=False
                    ))
                    seqs.append((start.line, 'block'))
                    indices.append(0)
                case tokens.FlowSequenceStartToken(start_mark=start, end_mark=endm):
                    emitter.emit(events.SequenceStartEvent(anchor=None,
                                                           tag=None,
                                                           implicit=1,
                                                           start_mark=start,
                                                           end_mark=endm,
                                                           flow_style=True
                                                           ))
                    seqs.append((start.line, 'flow'))
                    indices.append(0)
                # Before each block-sequence and flow-sequence entry, but we don't have to do anything with it
                case tokens.BlockEntryToken() | tokens.FlowEntryToken():
                   indices[-1] += 1
                case tokens.BlockEndToken():
                    _line, seq_type = seqs[-1]
                    # If an implicit map was open, it needs to be closed first
                    if seq_type == 'map':
                        emitter.emit(events.MappingEndEvent())
                        seqs.pop()
                        indices.pop()
                    # Otherwise, keep track of open sequence types
                    elif seq_type == 'block':
                        emitter.emit(events.SequenceEndEvent())
                        seqs.pop()
                        indices.pop()
                    else:
                        raise ValueError(seq_type)
                case tokens.FlowSequenceEndToken():
                    # After all items of a flow sequence ["a", "b"]
                    _line, seq_type = seqs[-1]
                    # If an implicit map was open, it needs to be closed first
                    if seq_type == 'map':
                        emitter.emit(events.MappingEndEvent())
                        seqs.pop()
                        indices.pop()
                    _line, seq_type = seqs[-1]
                    # Otherwise, keep track of open sequence types
                    if seq_type == 'flow':
                        emitter.emit(events.SequenceEndEvent())
                        seqs.pop()
                        indices.pop()
                    else:
                        raise ValueError(seq_type)
                case tokens.KeyToken(start_mark=start, end_mark=end_):
                    id, seq_type = seqs[-1]
                    if seq_type == 'map':
                        pass # Mapping already started, a scalar will follow
                    else:
                        # A key token may appear without a Mapping start token. Start a map.
                        seqs.append((start.line, 'map'))
                        indices.append(0)
                        emitter.emit(events.MappingStartEvent(anchor=None, tag=None, implicit=1))
                        # A scalar will follow, to be used as the key
                case tokens.ValueToken():
                    # Nothing to do: will be followed by a scalar. We already handled
                    # opening the implicit mapping in KeyToken
                    pass
                case tokens.BlockMappingStartToken(start_mark=start, end_mark=end_):
                    # Appears if we start a mapping in the block style
                    # - key: value
                    emitter.emit(events.MappingStartEvent(anchor=None, tag=None, implicit=1,
                                                          start_mark=start, end_mark=end_,
                                                          flow_style=False))
                    seqs.append((start.line, 'map'))
                    indices.append(0)
                case tokens.FlowMappingStartToken(start_mark=start, end_mark=end_):
                    # Appears if we start a flow style mapping, which is delimited by {} braces
                    emitter.emit(events.MappingStartEvent(anchor=None, tag=None, implicit=1,
                                                          start_mark=start, end_mark=end_,
                                                          flow_style=True))
                    seqs.append((start.line, 'map'))
                    indices.append(0)
                case tokens.FlowMappingEndToken():
                    _line, seq_type = seqs[-1]
                    # Track that we close maps properly
                    if seq_type == 'map':
                        emitter.emit(events.MappingEndEvent())
                        seqs.pop()
                        indices.pop()
                    else:
                        raise ValueError(seq_type)

                case tokens.StreamEndToken():
                    # Document fully parsed, emit requisite end markers and stop
                    emitter.emit(events.DocumentEndEvent())
                    emitter.emit(events.StreamEndEvent())
                    break

        return out.getvalue()

    
