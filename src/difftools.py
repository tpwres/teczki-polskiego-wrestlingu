import requests
import re
import sys
from pathlib import Path

def get_pr_diff(repo_path: str, pr_number: int, token: str, commit_sha: str | None = None) -> str:
    """
    Get the unified diff for the PR or a specific commit

    Args:
        repo_path (str): Repository path in 'owner/repo' format
        pr_number (int): Pull request number
        token (str): GitHub authentication token
        commit_sha (str, optional): Specific commit SHA to fetch diff for

    Returns:
        str: Unified diff for the PR or specified commit
    """
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3.diff"
    }
    repo_url = f"https://api.github.com/repos/{repo_path}"
    if commit_sha:
        # If commit_sha is provided, fetch diff for that specific commit
        url = f"{repo_url}/commits/{commit_sha}"
    else:
        # Otherwise, fetch PR diff as before
        url = f"{repo_url}/pulls/{pr_number}"

    response = requests.get(url, headers=headers)
    response.raise_for_status()

    return response.text

def parse_diff_positions(diff_content: str) -> dict[str, dict[int, int]]:
    """
    Parse diff content and create a mapping from file paths to line number -> position

    Returns:
        Dict with structure: {
            "path/to/file.py": {
                line_number: diff_position,
                ...
            }
        }
    """
    file_positions = {}
    current_file = None
    position = 0
    current_new_line = None
    lines = iter(diff_content.split('\n'))

    for line in lines:
        if line.startswith('diff --git'):
            # Extract file path from "diff --git a/path/file.py b/path/file.py"
            match = re.search(r'diff --git a/(.*?) b/', line)
            if match:
                current_file = match.group(1)
                file_positions[current_file] = {}
            else:
                raise ValueError(f"Could not match diff header {line}")
            position = -10000

        elif line.startswith('---') or line.startswith('+++'):
            # Skip past these header lines
            pass

        elif line.startswith('@@'):
            # Parse hunk header: @@ -old_start,old_count +new_start,new_count @@
            match = re.search(r'@@ -\d+(?:,\d+)? \+(\d+)(?:,\d+)? @@', line)
            if match and current_file:
                new_line_start = int(match.group(1))
                current_new_line = new_line_start
                position = 0
            elif current_file:
                raise ValueError(f"Could not match hunk header {line}")
            else:
                raise ValueError(f"Unexpected hunk header {line}")

        elif (current_file and current_new_line is not None
              and (line.startswith(' ') or line.startswith('+') or line.startswith('-'))):
            position += 1

            # Only map lines that are added or unchanged (not deleted)
            if line.startswith(' ') or line.startswith('+'):
                file_positions[current_file][current_new_line] = position
                current_new_line += 1
            # For deleted lines, don't increment new_line but still increment position
            elif line.startswith('-'):
                # Don't increment current_new_line for deleted lines
                pass

    return file_positions

def main():
    path = Path(sys.argv[1])
    content = path.read_text()
    positions = parse_diff_positions(content)
    print(f"{positions!r}")


if __name__ == "__main__":
    main()
