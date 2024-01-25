from pathlib import Path

class LintError:
    def supports_auto(self):
        return False

    def message(self, file_root: Path):
        return "LintError(???)"

    def calculate_fix(self, body_text):
        raise NotImplementedError

class Changeset:
    def apply_changes(self, path: Path):
        raise NotImplementedError
