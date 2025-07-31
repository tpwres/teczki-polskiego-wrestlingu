#!/usr/bin/env python3
"""
post_review.py - Posts automated review comments to GitHub PR
"""

import json
import os
import requests
import sys
from typing import cast
from difftools import get_pr_diff, parse_diff_positions


def convert_line_to_position(comments: list[dict], file_positions: dict[str, dict[int, int]]) -> list[dict]:
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

def get_latest_commit_sha(repo_path: str, pr_number: int, token: str) -> str:
    """
    Get the latest commit SHA for the PR by efficiently fetching the last page of commits

    Args:
        repo_path (str): Repository path in format 'owner/repo'
        pr_number (int): Pull request number
        token (str): GitHub authentication token

    Returns:
        str: SHA of the latest commit in the PR
    """
    base_url = f"https://api.github.com/repos/{repo_path}/pulls/{pr_number}/commits"
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json"
    }

    # First, fetch the first page to check pagination
    initial_response = requests.get(base_url, headers=headers)
    initial_response.raise_for_status()

    # If Link header exists, extract the last page URL
    link_header = initial_response.headers.get('Link', '')

    if link_header:
        # Parse the Link header to find the last page URL
        last_page_url = None
        for link in link_header.split(', '):
            target, _semi, relname = link.partition(';')
            if 'rel="last"' in relname:
                last_page_url = target.strip('<>')
                break

        # If last page URL found, fetch commits from the last page
        if last_page_url:
            last_page_response = requests.get(last_page_url, headers=headers)
            last_page_response.raise_for_status()
            commits = last_page_response.json()
        else:
            # Fallback to initial response if no last page found
            commits = initial_response.json()
    else:
        # No pagination, use initial response
        commits = initial_response.json()

    # Validate commit list
    if not commits:
        raise ValueError("No commits found in PR")

    # Return SHA of the last commit
    return commits[-1]["sha"]


def post_review_with_comments(repo_path: str, pr_number: int,
                            commit_sha: str, comments: list[dict], token: str) -> None:
    """Post a review with multiple comments using positions"""
    url = f"https://api.github.com/repos/{repo_path}/pulls/{pr_number}/reviews"
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
    print(review_data)

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
    pr_number = int(cast(str, os.getenv("PR_NUMBER")))
    repo_path = os.getenv("REPO_PATH")
    report_file = os.getenv("REPORT_FILE", "analysis.json")  # Default fallback

    if not all([token, pr_number, repo_path]):
        print("❌ Missing required environment variables")
        sys.exit(1)

    repo_path = cast(str, repo_path)
    token = cast(str, token)

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
        commit_sha = get_latest_commit_sha(repo_path, pr_number, token)
        print(f"Latest commit SHA: {commit_sha}")

        # Get PR diff and parse positions
        print("📄 Fetching PR diff...")
        diff_content = get_pr_diff(repo_path, pr_number, token)
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
        post_review_with_comments(repo_path, pr_number, commit_sha, positioned_comments, token)

    except requests.exceptions.RequestException as e:
        print(f"❌ API request failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
