#!/usr/bin/env python3
"""
Git Commit History Analyzer
Reads git commit history from the last 7 days and groups changes by filename and date.
"""

import subprocess
import sys
from datetime import datetime, timedelta
from collections import defaultdict
import json
import re
from pathlib import Path
from contextlib import contextmanager
import tomllib

def find_renamed_file(original_filename):
    """Find the current name of a file that may have been renamed"""
    # Get rename history from git log
    command = 'git log -m --first-parent --diff-filter=R --name-status'
    output = run_git_command(command)

    if not output:
        return original_filename

    # Parse the output to find renames
    lines = output.split('\n')
    current_name = original_filename

    for line in lines:
        line = line.strip()
        # Look for rename entries (format: R<similarity>\told_name\tnew_name)
        if line.startswith('R') and '\t' in line:
            # Split on tabs to get old and new names
            parts = line.split('\t')
            if len(parts) >= 3:
                old_name = parts[1]
                new_name = parts[2]

                # If we found a rename from our current tracked name
                if old_name == current_name:
                    current_name = new_name
                    break

    return current_name


@contextmanager
def git_file_content(filename):
    """Context manager to safely read file content from git HEAD, handling renames"""
    try:
        # First try to read the file directly
        command = f'git show HEAD:{filename}'
        content = run_git_command(command)

        # If that failed, try to find if the file was renamed
        if content is None:
            renamed_file = find_renamed_file(filename)
            if renamed_file != filename:
                command = f'git show HEAD:{renamed_file}'
                content = run_git_command(command)

        yield content
    except Exception:
        yield None

def extract_toml_frontmatter(content):
    """Extract and parse TOML frontmatter from content delimited by +++"""
    if not content:
        return None

    lines = content.split('\n')
    if not lines or lines[0] != '+++':
        return None
    
    # Find the closing +++
    frontmatter_lines = []
    for i, line in enumerate(lines[1:], 1):
        if line == '+++':
            break
        frontmatter_lines.append(line)
    else:
        # No closing +++ found
        return None

    if not frontmatter_lines:
        return None

    # Parse TOML frontmatter
    frontmatter_content = '\n'.join(frontmatter_lines)
    try:
        return tomllib.loads(frontmatter_content)
    except tomllib.TOMLDecodeError:
        return None

def get_gallery_title(filename):
    """Extract title from corresponding markdown file for gallery TOML files"""
    # Extract the prefix (everything before -gallery.toml)
    prefix = filename.replace('-gallery.toml', '')
    corresponding_md = f"{prefix}.md"

    with git_file_content(corresponding_md) as content:
        frontmatter_data = extract_toml_frontmatter(content)
        if frontmatter_data:
            title = frontmatter_data.get('title')
            if title:
                return f"{title} Gallery ({filename})"

    return f"Gallery ({filename})"

def get_geojson_title(filename):
    """Extract properties.name from GeoJSON files"""
    with git_file_content(filename) as content:
        if not content:
            return filename

        # Parse JSON
        try:
            geojson_data = json.loads(content)

            # Look for properties.name in various GeoJSON structures
            name = None

            # Single feature
            if geojson_data.get('type') == 'Feature':
                properties = geojson_data.get('properties', {})
                name = properties.get('name')

            # Feature collection - use first feature's name
            elif geojson_data.get('type') == 'FeatureCollection':
                features = geojson_data.get('features', [])
                if features and len(features) > 0:
                    properties = features[0].get('properties', {})
                    name = properties.get('name')
                    if len(features) > 1:
                        name = f"{name} (+{len(features)-1} more features)" if name else f"{len(features)} features"

            if name:
                return f"{name} ({filename})"

        except json.JSONDecodeError:
            pass
    
    return filename

def get_md_title(filename):
    """Extract title from TOML frontmatter in .md files"""
    with git_file_content(filename) as content:
        frontmatter_data = extract_toml_frontmatter(content)
        if frontmatter_data:
            title = frontmatter_data.get('title')
            if title:
                return f"{title} ({filename})"
    
    return filename

# Filename to title mapping for files without title extraction logic
# Keys can be exact filenames or shell patterns (using pathlib.match)
# Values can be strings or functions that take filename and return title
FILENAME_TO_TITLE = {
    "const/name-to-flag.yaml": "Country Flags",
    "*.md": get_md_title,
    "*.geojson": get_geojson_title,
    "*-gallery.toml": get_gallery_title,
    # Add more filename mappings here as needed
    # "config/settings.json": "Application Settings",
    # "data/users.csv": "User Database",
}

def run_git_command(command):
    """Run a git command and return the output"""
    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        #print(f"Error running git command: {e}")
        #print(f"Command: {command}")
        #print(f"Error output: {e.stderr}")
        return None

def get_display_name(filename):
    """Get display name for different file types"""
    # Check filename mappings (exact matches and patterns)
    path_obj = Path(filename)

    # First check for exact matches
    match FILENAME_TO_TITLE.get(filename):
        case resolver if callable(resolver):
            return resolver(filename)
        case str(name):
            return name

    for pattern, value in FILENAME_TO_TITLE.items():
        # If there was an exact match, we returned earlier.
        if not path_obj.match(pattern):
            continue
        match value:
            case resolver if callable(resolver):
                return resolver(filename)
            case str(name): # Not really used
                return f"{name} ({filename})"

    return filename

def get_commits_last_7_days():
    """Get all commits from the last 7 days, excluding merge PR commits"""
    seven_days_ago = datetime.now() - timedelta(days=7)
    since_date = seven_days_ago.strftime('%Y-%m-%d')

    # Get commit hashes and basic info
    command = f'git log --since="{since_date}" --pretty=format:"%H|%ad|%an|%s" --date=short'
    output = run_git_command(command)

    if not output:
        return []

    commits = []
    for line in output.split('\n'):
        if line.strip():
            parts = line.split('|', 3)
            if len(parts) == 4:
                hash_val, date, author, message = parts

                # Skip merge pull request commits
                if is_merge_pr_commit(message):
                    continue

                commits.append({
                    'hash': hash_val,
                    'date': date,
                    'author': author,
                    'message': message
                })

    return commits

def get_file_changes(commit_hash):
    """Get file changes for a specific commit"""
    command = f'git show --numstat --format="" {commit_hash}'
    output = run_git_command(command)

    if not output:
        return []

    changes = []
    for line in output.split('\n'):
        if line.strip():
            parts = line.split('\t')
            if len(parts) >= 3:
                additions = parts[0] if parts[0] != '-' else '0'
                deletions = parts[1] if parts[1] != '-' else '0'
                filename = '\t'.join(parts[2:])  # Handle filenames with tabs

                try:
                    additions_int = int(additions)
                    deletions_int = int(deletions)

                    changes.append({
                        'filename': filename,
                        'additions': additions_int,
                        'deletions': deletions_int
                    })
                except ValueError:
                    # Handle binary files or other special cases
                    changes.append({
                        'filename': filename,
                        'additions': 0,
                        'deletions': 0,
                        'binary': True
                    })

    return changes

def is_merge_pr_commit(message):
    """Check if a commit message is a merge pull request"""
    # Match patterns like "Merge pull request #123", "Merge pull request #456 from..."
    pattern = r'^Merge pull request #\d+'
    return bool(re.match(pattern, message))

def format_line_changes(additions, deletions, is_binary=False):
    """Format line changes as +X -Y or indicate binary"""
    if is_binary:
        return "(binary)"

    parts = []
    if additions > 0:
        parts.append(f"+{additions}")
    if deletions > 0:
        parts.append(f"-{deletions}")

    if not parts:
        return "(no changes)"

    return " ".join(parts)

def format_file_changeset_md(filename, changes_list):
    """Format a file's changeset information as Markdown"""
    # Get display name (use title for .md files, name for .geojson files)
    display_name = get_display_name(filename)

    # Aggregate changes for the same file on the same date
    total_additions = sum(c['additions'] for c in changes_list)
    total_deletions = sum(c['deletions'] for c in changes_list)
    authors = list(set(c['author'] for c in changes_list))
    has_binary = any(c.get('binary', False) for c in changes_list)

    # Format the output
    authors_str = ", ".join(authors) if len(authors) <= 2 else f"{authors[0]} and {len(authors)-1} others"
    changes_str = format_line_changes(total_additions, total_deletions, has_binary)

    # Build the formatted output as markdown list item with line breaks
    lines = []

    # Show commit messages for this file (limit to 2 most recent)
    messages = [c['message'] for c in changes_list]
    unique_messages = list(dict.fromkeys(messages))  # Remove duplicates while preserving order

    # Build single list item with line breaks
    content_parts = [f"**{display_name}**"]
    content_parts.append(f"Author(s): {authors_str}")
    content_parts.append(f"Changes: `{changes_str}`")

    for i, msg in enumerate(unique_messages[:2]):
        truncated_msg = msg[:80] + "..." if len(msg) > 80 else msg
        content_parts.append(truncated_msg)

    if len(unique_messages) > 2:
        content_parts.append(f"... and {len(unique_messages) - 2} more commit(s)")

    # Join all parts with markdown line breaks
    content = " \\\n  ".join(content_parts)
    lines.append(f"- {content}")

    return "\n".join(lines)

def format_date_header(date, markdown=False):
    """Format a date header with separator"""
    if markdown:
        return f"## {date}\n"
    else:
        lines = []
        lines.append(f"\n📅 {date}")
        lines.append("-" * 40)
        return "\n".join(lines)

def analyze_repository():
    """Main function to analyze the repository"""
    commits = get_commits_last_7_days()

    if not commits:
        print("No commits found in the last 7 days.")
        return

    # Group data by date, then by filename
    data_by_date = defaultdict(lambda: defaultdict(list))

    for commit in commits:
        changes = get_file_changes(commit['hash'])

        for change in changes:
            data_by_date[commit['date']][change['filename']].append({
                'author': commit['author'],
                'message': commit['message'],
                'additions': change['additions'],
                'deletions': change['deletions'],
                'binary': change.get('binary', False)
            })

    # Sort dates in descending order (most recent first)
    sorted_dates = sorted(data_by_date.keys(), reverse=True)

    for date in sorted_dates:
        print(format_date_header(date, markdown=True))

        # Sort filenames alphabetically
        sorted_filenames = sorted(data_by_date[date].keys())

        for filename in sorted_filenames:
            # Ignore changes not under content/
            if not Path(filename).is_relative_to('content'):
                continue
            changes_list = data_by_date[date][filename]
            formatted_output = format_file_changeset_md(filename, changes_list)
            print(formatted_output, end="\n")

if __name__ == "__main__":
    analyze_repository()
