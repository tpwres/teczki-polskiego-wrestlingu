#!/usr/bin/env python3
"""
post_review.py - Posts automated review comments to GitHub PR
"""

import json
import os
import re
import requests
import sys
from typing import List, Dict

def get_pr_diff(owner: str, repo: str, pr_number: int, token: str) -> str:
    """Get the unified diff for the PR"""
    url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{pr_number}"
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3.diff"
    }

    response = requests.get(url, headers=headers)
    response.raise_for_status()

    return response.text

def parse_diff_positions(diff_content: str) -> Dict[str, Dict[int, int]]:
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

    for line in diff_content.split('\n'):
        if line.startswith('diff --git'):
            # Extract file path from "diff --git a/path/file.py b/path/file.py"
            match = re.search(r'diff --git a/(.*?) b/', line)
            if match:
                current_file = match.group(1)
                file_positions[current_file] = {}
            position = 0

        elif line.startswith('@@'):
            # Parse hunk header: @@ -old_start,old_count +new_start,new_count @@
            match = re.search(r'@@ -\d+(?:,\d+)? \+(\d+)(?:,\d+)? @@', line)
            if match and current_file:
                new_line_start = int(match.group(1))
                current_new_line = new_line_start
                position = 0  # Reset position for this hunk

        elif current_file and current_new_line is not None and (line.startswith(' ') or line.startswith('+') or line.startswith('-')):
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

def convert_line_to_position(comments: List[Dict], file_positions: Dict[str, Dict[int, int]]) -> List[Dict]:
    """Convert line-based comments to position-based comments"""
    positioned_comments = []

    for comment in comments:
        path = comment["path"]
        line = comment.get("line", 1)
        message = comment["message"]

        # Check if we have position mapping for this file
        if path not in file_positions:
            print(f"⚠️ Skipping comment on '{path}': file not in diff")
            continue

        # Check if this line has a position in the diff
        if line not in file_positions[path]:
            print(f"⚠️ Skipping comment on '{path}:{line}': line not in diff")
            continue

        position = file_positions[path][line]
        positioned_comments.append({
            "path": path,
            "position": position,
            "body": message
        })

        print(f"✅ Mapped {path}:{line} -> position {position}")

    return positioned_comments
    """Get the latest commit SHA for the PR"""
    url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{pr_number}/commits"
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json"
    }

    response = requests.get(url, headers=headers)
    response.raise_for_status()

    commits = response.json()
    if not commits:
        raise ValueError("No commits found in PR")

    return commits[-1]["sha"]

def get_latest_commit_sha(owner: str, repo: str, pr_number: int, token: str) -> str:
    """Get the latest commit SHA for the PR"""
    url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{pr_number}/commits"
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json"
    }

    response = requests.get(url, headers=headers)
    response.raise_for_status()

    commits = response.json()
    if not commits:
        raise ValueError("No commits found in PR")

    return commits[-1]["sha"]

def post_review_with_comments(owner: str, repo: str, pr_number: int, 
                            commit_sha: str, comments: List[Dict], token: str) -> None:
    """Post a review with multiple comments using positions"""
    url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{pr_number}/reviews"
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json"
    }
    
    # Comments should already have position instead of line
    review_data = {
        "commit_id": commit_sha,
        "body": f"🤖 Automated code review found {len(comments)} suggestion(s)",
        "event": "COMMENT",
        "comments": comments  # Comments already formatted with position
    }
    
    response = requests.post(url, headers=headers, json=review_data)
    
    if response.status_code == 200:
        print(f"✅ Successfully posted review with {len(comments)} comments")
    else:
        print(f"❌ Failed to post review: {response.status_code}")
        print(f"Response: {response.text}")
        sys.exit(1)

def main():
    # Get environment variables
    token = os.getenv("GITHUB_TOKEN")
    pr_number = int(os.getenv("PR_NUMBER"))
    owner = os.getenv("REPO_OWNER")
    repo = os.getenv("REPO_NAME")
    report_file = os.getenv("REPORT_FILE", "analysis.json")  # Default fallback

    if not all([token, pr_number, owner, repo]):
        print("❌ Missing required environment variables")
        sys.exit(1)

    print(f"📄 Reading report from: {report_file}")

    # Read analysis results
    try:
        with open(report_file, "r") as f:
            analysis_data = json.load(f)
    except FileNotFoundError:
        print(f"❌ Report file '{report_file}' not found")
        sys.exit(1)
    except json.JSONDecodeError:
        print(f"❌ Invalid JSON in '{report_file}'")
        sys.exit(1)

    comments = analysis_data

    if not comments:
        print("ℹ️ No comments to post")
        return

    try:
        # Get the latest commit SHA
        commit_sha = get_latest_commit_sha(owner, repo, pr_number, token)
        print(f"Latest commit SHA: {commit_sha}")

        # Get PR diff and parse positions
        print("📄 Fetching PR diff...")
        diff_content = get_pr_diff(owner, repo, pr_number, token)
        file_positions = parse_diff_positions(diff_content)

        print(f"📊 Found diff positions for {len(file_positions)} files")
        for file_path, positions in file_positions.items():
            print(f"  {file_path}: {len(positions)} lines")

        # Convert line-based comments to position-based comments
        positioned_comments = convert_line_to_position(comments, file_positions)

        if not positioned_comments:
            print("⚠️ No comments could be mapped to diff positions")
            print("This usually means your analysis tool is reporting lines that aren't part of the PR changes")
            return

        print(f"✅ Successfully mapped {len(positioned_comments)}/{len(comments)} comments to diff positions")

        # Post 

        post_review_with_comments(owner, repo, pr_number, commit_sha, positioned_comments, token)

    except requests.exceptions.RequestException as e:
        print(f"❌ API request failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
