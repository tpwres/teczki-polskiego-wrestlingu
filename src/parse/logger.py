from contextlib import contextmanager
import logging
import threading
import traceback
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional

class IssueLevel(Enum):
    WARNING = "warning"
    ERROR = "error"
    FATAL = "fatal"

@dataclass
class ParseIssue:
    level: IssueLevel
    message: str
    component: str
    # Extra info
    location: Optional[str] = None
    line_number: Optional[int] = None
    column_number: Optional[int] = None
    # Really extra
    exception: Optional[Exception] = None
    traceback: Optional[str] = None
    context: dict[str, Any] = field(default_factory=dict)

    def __str__(self) -> str:
        loc_info = ""
        if self.location:
            loc_info += f" at {self.location}"
        if self.line_number:
            loc_info += f":{self.line_number}"
        if self.column_number:
            loc_info += f":{self.column_number}"

        return f"[{self.level.value.upper()} {self.component}{loc_info}: {self.message}"

class ParseContext:
    def __init__(self):
        # Thread-local is a bit overkill but no harm
        self._local = threading.local()

    @property
    def current_component(self) -> str:
        return getattr(self._local, 'component', '[root]')

    @current_component.setter
    def current_component(self, value: str):
        self._local.component = value

    @property
    def current_location(self) -> str:
        return getattr(self._local, 'location', None)

    @current_location.setter
    def current_location(self, value: str):
        self._local.location = value

    @property
    def context_stack(self) -> list[str]:
        if not hasattr(self._local, 'stack'):
            self._local.stack = []

        return self._local.stack

    def push_context(self, component: str, location: Optional[str] = None):
        self.context_stack.append(f"{self.current_component}:{self.current_location or 'unknown'}")
        self.current_component = component
        self.current_location = location

    def pop_context(self):
        if not self.context_stack:
            return

        prev_context = self.context_stack.pop()
        component, location = prev_context.split(':', 1)
        self.current_component = component
        self.current_location = location

    def get_full_context(self) -> str:
        full_path = [
            entry.split(':', 1)[0]
            for entry in self.context_stack
        ]
        full_path.append(self.current_component)
        return " > ".join(full_path)

class RichDocLogger:
    def __init__(self, logger_name: str = "RichDocParser"):
        self.logger = logging.getLogger(logger_name)
        self.issues: List[ParseIssue] = []
        self.context = ParseContext()
        self._setup_logger()

    def _setup_logger(self):
        if self.logger.handlers: return

        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            "[%(asctime)s] %(levelname)s | %(name)s | %(message)s"
        )
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)
        self.logger.setLevel(logging.INFO)

    def log_warning(self, message: str, **kwargs):
        self._log_issue(IssueLevel.WARNING, message, **kwargs)

    def log_error(self, message: str, **kwargs):
        self._log_issue(IssueLevel.ERROR, message, **kwargs)

    def log_fatal(self, message: str, **kwargs):
        self._log_issue(IssueLevel.FATAL, message, **kwargs)

    def log_exception(self, message: str, exc: Exception, **kwargs):
        kwargs.update(exception=exc, traceback=traceback.format_exception(exc))
        self._log_issue(IssueLevel.ERROR, message, **kwargs)

    def _log_issue(self, level, message: str, **kwargs):
        issue = ParseIssue(
            level=level,
            message=message,
            component=self.context.current_component,
            location=self.context.current_location,
            **kwargs
        )
        self.issues.append(issue)

        log_method = getattr(self.logger, level.value)
        context = f"({self.context.get_full_context()}) {message}"
        log_method(context)

    @contextmanager
    def parsing_context(self, component: str, location: Optional[str] = None):
        self.context.push_context(component, location)
        try:
            yield
        finally:
            self.context.pop_context()

    def has_errors(self) -> bool:
        return any(issue.level in [IssueLevel.ERROR, IssueLevel.FATAL] for issue in self.issues)

    def print_report(self, stream):
        breakpoint()
