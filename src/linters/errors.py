from .base import LintError
from dataclasses import dataclass
from typing import Optional
from pathlib import Path
from yaml import MarkedYAMLError, YAMLError

def format_error(message, filename, line, col):
    if col is not None and line is not None:
        return f"{filename}:{line}:{col} {message}"
    elif line is not None:
        return f"{filename}:{line} {message}"
    else:
        return f"{filename} {message}"

class ErrorSink:
    def __init__(self):
        self.messages = []

    def error(self, message):
        self.messages.append('E' + message)

    def warning(self, message):
        self.messages.append('W' + message)

    def parse_error(self, parse_error, filename, line_offset):
        # Parse error wraps some sort of message from the parser bowels
        (original_error,) = parse_error.args
        match original_error:
            case YAMLError() as y:
                self.error(self.convert_yaml_error(y, filename, line_offset))

    def convert_yaml_error(self, yaml_error, filename, line_offset) -> str:
        match yaml_error:
            case MarkedYAMLError(problem=problem, problem_mark=mark, context_mark=cmark, context=context) if mark and cmark:
                return format_error(f"{problem} {context} at {cmark.line + line_offset}:{cmark.column}", filename, mark.line + line_offset, mark.column)
            case MarkedYAMLError(problem=problem, problem_mark=mark) if mark:
                return format_error(problem, filename, mark.line + line_offset, mark.column)
            case MarkedYAMLError(problem=problem):
                return format_error(problem, filename, None, None)
            case err:
                breakpoint()
                return f"{filename} {err}"

class ConsoleErrorSink(ErrorSink):

    def error(self, message):
        super().error(message)
        print("[E] " + message)

    def warning(self, message):
        super().warning(message)
        print("[W] " + message)


@dataclass
class FileError(LintError):
    path: Optional[Path]
    text: str

    def message(self, file_root: Optional[Path]):
        match self.path:
            case Path():
                if file_root:
                    return f'[{self.path.relative_to(file_root)}] Error: {self.text}'
                else:
                    return f'[{self.path}] Error: {self.text}'
            case _:
                return f'[????] Error: {self.text}'

    @property
    def supports_auto(self):
        return False

    @property
    def fatal(self):
        return True

class LintWarning(LintError): pass

@dataclass
class FileWarning(LintWarning):
    path: Optional[Path]
    text: str

    def message(self, file_root: Optional[Path]):
        match self.path:
            case Path():
                if file_root:
                    return f'[{self.path.relative_to(file_root)}] Warning: {self.text}'
                else:
                    return f'[{self.path}] Warning: {self.text}'
            case _:
                return f'[????] Warning: {self.text}'

    @property
    def supports_auto(self):
        return False

    @property
    def fatal(self):
        return False
