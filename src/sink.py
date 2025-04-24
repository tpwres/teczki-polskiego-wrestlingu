from yaml import MarkedYAMLError, YAMLError
from warnings import warn
from errors import format_error

class Sink:
    def __init__(self):
        self.errors = []
        self.warnings = []

    @property
    def empty(self):
        return len(self.errors) == 0

    def error(self, message):
        self.errors.append(message)

    def warning(self, message):
        self.warnings.append(message)

    def dump(self, stream):
        # XXX: This is unsorted and probably not very helpful
        for m in self.warnings:
            stream.write(f'Warning: {m}\n')

        for m in self.errors:
            stream.write(f'Error: {m}\n')

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

class NullSink(Sink):
    def error(self, message):
        pass

    def warning(self, message):
        pass

class ConsoleSink(Sink):
    def error(self, message):
        super().error(message)
        print(f"[E] {message}")

    def warning(self, message):
        super().warning(message)
        print(f"[W] {message}")

class ExplosiveSink(Sink):
    def error(self, message):
        raise Exception(message)

    def warning(self, message):
        warn(message)

