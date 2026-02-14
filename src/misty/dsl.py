from typing import Optional, Any, Protocol, Sequence, Literal, runtime_checkable, ClassVar, Callable
from dataclasses import dataclass
from enum import IntEnum
from pathlib import Path
from abc import ABC, abstractmethod
from functools import singledispatchmethod

Token = tuple[str, tuple[int, int], tuple]
TokenMatchFn = Callable[[str, tuple[int, int], tuple], bool]
ProcessSingleNodeFn = Callable[[Token], Optional[Token]]
ProcessManyNodesFn = Callable[[list[Token]], Optional[list[Token]]]

class Level(IntEnum):
    INFO = 0
    WARNING = 10
    ERROR = 20

@runtime_checkable
class Fixable(Protocol):
    def fix(self, token: Token) -> Token | None:
        """Returns an automatically fixed version of the element."""
        raise NotImplemented

@dataclass(frozen=True)
class Message:
    text: str
    location: tuple[int, int]
    level: Level

    def format(self, path: str):
        row, col = self.location
        return f'{path}:{row:02d}:{col:02d} | {self.level._name_} | {self.text}'

class SingleMatch:
    def __init__(self, type: Optional[str]=None, fn: TokenMatchFn = lambda _1, _2, _3: True):
        self.node_type = type
        self.matchfn = fn

    def __or__(self, other):
        return AnySingleMatch(self, other)

    def matches(self, node: Token):
        node_type, pos, rest = node
        if self.node_type and node_type != self.node_type:
            return False

        if not self.matchfn(node_type, pos, rest):
            return False

        return True

class AnySingleMatch:
    def __init__(self, left: SingleMatch|AnySingleMatch, right: SingleMatch|AnySingleMatch):
        self.left = left
        self.right = right

    def __or__(self, other):
        return AnySingleMatch(self, other)

    def matches(self, node: Token):
        return self.left.matches(node) or self.right.matches(node)

class ChainMatch:
    # TBD
    pass


class Rule(ABC):
    pattern: ClassVar[SingleMatch|AnySingleMatch|ChainMatch]

    @abstractmethod
    def process(self, nodes: List[Token]) -> Optional[List[Token]]:
        """Process matched nodes, returns new nodes to replace them or None to keep original nodes."""
        pass

class RuleRunner:
    def __init__(self, rules: List[Rule]):
        self.rules = rules

    def apply(self, doc: List[Token]) -> List[Message]:
        diagnostics: List[Message] = []

        for rule in self.rules:
            messages = self.apply_rule(rule.pattern, rule.describe, doc)
            if messages:
                diagnostics.extend(messages)

            print(f"{rule} | {diagnostics}")

        return diagnostics

    @singledispatchmethod
    def apply_rule(self, pattern, describe, doc: List[Token]) -> List[Message]:
        raise NotImplementedError(f"Cannot apply pattern {type(pattern)}")

    @apply_rule.register
    def apply_singlematch(self, pattern: SingleMatch|AnySingleMatch, describe: Callable, doc: List[Token]) -> List[Message]:
        messages: List[Message] = []
        for node in doc:
            if not pattern.matches(node):
                continue
            diagnostics = describe(node)
            messages.extend(diagnostics or [])

        return messages

class RuleApplier:
    def __init__(self, rules: List[Rule]):
        self.rules = rules

    def apply(self, doc: List[Token]) -> List[Token]:
        result = doc.copy()

        for rule in self.rules:
            result = self.apply_rule(rule.pattern, rule.process, result)

        return result

    @singledispatchmethod
    def apply_rule(self, pattern, process, doc: List[Token]) -> List[Token]:
        raise NotImplementedError(f"Cannot apply pattern of type {type(pattern)}")

    @apply_rule.register
    def apply_singlematch(self, pattern: SingleMatch|AnySingleMatch, process: ProcessSingleNodeFn, doc: List[Token]) -> List[Token]:
        result = []
        for node in doc:
            if pattern.matches(node):
                if updated := process(node):
                    result.extend(updated)
                else:
                    result.append(node)
            else:
                result.append(node)

        return result

    @apply_rule.register
    def apply_chain(self, pattern: ChainMatch, process: ProcessManyNodesFn, doc: List[Token]) -> List[Token]:
        result, i, chain_len = [], 0, len(rule)

        while i < len(doc):
            if i <= len(doc) - chain_len:
                slice = doc[i:i + chain_len]
                matched = all(pattern.matchers[j].matches(slice[j])
                              for j in range(chain_len))
                if matched:
                    if updated := process(slice):
                        result.extend(updated)
                    else:
                        result.extend(slice)

                    i += chain_len
                    continue

            result.append(doc[i])
            i += 1

        return result


    


