#!/usr/bin/env python3

import json
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List

import requests
from github import Auth, Github


class GitHubIssueMonitor:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        github_token = os.getenv("GITHUB_TOKEN")
        if not github_token:
            raise ValueError("GITHUB_TOKEN environment variable is required")
        auth = Auth.Token(github_token)
        self.github = Github(auth=auth)
        self.cache_file = Path(f"cache/{config['name']}-cache.json")

    def load_cache(self) -> Dict[str, Any]:
        """Load cache file or return empty cache if not found."""
        try:
            if self.cache_file.exists():
                with open(self.cache_file, "r") as f:
                    return json.load(f)
        except Exception as e:
            print(f"⚠️  Warning: Could not load cache: {e}")
        return {"notified_issues": []}

    def save_cache(self, cache: Dict[str, Any]):
        """Save cache to file."""
        self.cache_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.cache_file, "w") as f:
            json.dump(cache, f, indent=2)

    def build_search_query(self) -> str:
        """Build GitHub search query from configuration."""
        # Combine search phrases with OR
        phrases = " OR ".join(f'"{phrase}"' for phrase in self.config["searchPhrases"])
        query = f"({phrases}) type:issue"

        # Add time filter for recent issues
        hours_ago = self.config.get("lookbackHours", 24)
        date = (datetime.now() - timedelta(hours=hours_ago)).strftime("%Y-%m-%d")
        query += f" created:>={date}"

        # Automatically exclude the repository where this tool is deployed
        # This prevents the tool from detecting issues it creates in its own repo
        deployment_repo = os.getenv("GITHUB_REPOSITORY")
        if deployment_repo:
            query += f" -repo:{deployment_repo}"
            print(f"🚫 Auto-excluding deployment repository: {deployment_repo}")

        # Exclude repositories
        if excluded_repos := self.config.get("excludedRepos", []):
            excluded = " ".join(f"-repo:{repo}" for repo in excluded_repos)
            query += f" {excluded}"

        # Exclude organizations
        if excluded_orgs := self.config.get("excludedOrgs", []):
            excluded = " ".join(f"-org:{org}" for org in excluded_orgs)
            query += f" {excluded}"

        return query

    def search_issues(self) -> List[Dict[str, Any]]:
        """Search for issues using GitHub API."""
        query = self.build_search_query()
        print(f"🔍 Searching with query: {query}")

        try:
            # Use GitHub Search API
            issues = self.github.search_issues(query, sort="created", order="desc")

            # Convert to dict format and filter out PRs
            results = []
            for issue in issues:
                if not hasattr(issue, "pull_request") or issue.pull_request is None:
                    results.append(
                        {
                            "id": issue.id,
                            "title": issue.title,
                            "html_url": issue.html_url,
                            "repository": issue.repository.full_name,
                            "user": issue.user.login,
                            "created_at": issue.created_at.isoformat(),
                            "body": issue.body or "",
                        }
                    )

            return results

        except Exception as e:
            print(f"❌ Error searching issues: {e}")
            raise

    def is_excluded(self, issue: Dict[str, Any]) -> bool:
        """Check if issue should be excluded based on config."""
        repo = issue["repository"]
        org = repo.split("/")[0]

        if repo in self.config.get("excludedRepos", []):
            return True

        if org in self.config.get("excludedOrgs", []):
            return True

        return False

    def is_non_english(self, issue: Dict[str, Any]) -> bool:
        """Check if issue appears to be in a non-English language."""
        import sys

        # Debug: Log entry and config value
        filter_enabled = self.config.get("filterNonEnglish", False)
        print(
            f"   [DEBUG] is_non_english called for: {issue['title'][:40]}...",
            flush=True,
        )
        print(
            f"   [DEBUG] filterNonEnglish={filter_enabled} "
            f"(type={type(filter_enabled).__name__})",
            flush=True,
        )

        # Only filter if language filtering is enabled
        if not filter_enabled:
            print("   [DEBUG] Language filtering disabled, returning False", flush=True)
            return False

        try:
            from langdetect import LangDetectException, detect

            # Combine title and first 500 chars of body for language detection
            # Limiting body length prevents spam URLs from overwhelming the
            # actual content and causing false "English" detection
            body_sample = issue["body"][:500] if issue["body"] else ""
            text = f"{issue['title']} {body_sample}"
            text_len = len(text.strip())
            print(f"   [DEBUG] Text length (truncated): {text_len}", flush=True)

            # Skip if text is too short (< 20 chars) to avoid false positives
            if text_len < 20:
                print("   [DEBUG] Text too short, skipping detection", flush=True)
                return False

            # Detect language
            detected_lang = detect(text)
            print(f"   [DEBUG] Detected language: {detected_lang}", flush=True)

            # Return True if not English (langdetect uses 'en' for English)
            if detected_lang != "en":
                print(
                    f"   🌐 Filtered non-English issue ({detected_lang}): "
                    f"{issue['title'][:50]}...",
                    flush=True,
                )
                return True
            else:
                print("   [DEBUG] Issue is English, not filtering", flush=True)

        except LangDetectException:
            # If detection fails, don't filter it out (benefit of doubt)
            print(
                f"   ⚠️  Could not detect language for: {issue['title'][:50]}...",
                flush=True,
            )
            return False
        except Exception as e:
            print(f"   ⚠️  Language detection error: {e}", flush=True)
            import traceback

            traceback.print_exc()
            sys.stdout.flush()
            return False

        return False

    def send_slack_notification(self, issues: List[Dict[str, Any]]):
        """Send Slack notification with new issues."""
        slack_config = self.config.get("notifications", {}).get("slack", {})

        if not slack_config.get("enabled", False):
            return

        webhook_url = slack_config.get("webhookUrl") or os.getenv("SLACK_WEBHOOK_URL")
        if not webhook_url:
            print("⚠️  Slack enabled but no webhook URL configured")
            return

        # Build Slack message
        count = len(issues)
        phrases = ", ".join(f'"{phrase}"' for phrase in self.config["searchPhrases"])

        # Create rich Slack message with blocks
        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": f"🔍 {count} new GitHub issue"
                    + f"{'s' if count > 1 else ''} found!",
                },
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"Found *{count}* new GitHub issue"
                    + f"{'s' if count > 1 else ''} matching {phrases}",
                },
            },
            {"type": "divider"},
        ]

        # Add each issue as a block (limit to 10 for Slack limits)
        for issue in issues[:10]:
            repo_link = (
                f"<https://github.com/{issue['repository']}" f"|{issue['repository']}>"
            )
            issue_link = f"<{issue['html_url']}|{issue['title']}>"
            author_link = f"<https://github.com/{issue['user']}|@{issue['user']}>"
            created_date = datetime.fromisoformat(
                issue["created_at"].replace("Z", "+00:00")
            ).strftime("%Y-%m-%d %H:%M UTC")

            blocks.append(
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*{issue_link}*\n📁 {repo_link} | "
                        + f"👤 {author_link} | 📅 {created_date}",
                    },
                    "accessory": {
                        "type": "button",
                        "text": {"type": "plain_text", "text": "View Issue"},
                        "url": issue["html_url"],
                        "action_id": f"view_issue_{issue['id']}",
                    },
                }
            )

        if len(issues) > 10:
            blocks.append(
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"_... and {len(issues) - 10} more issue"
                        + f"{'s' if len(issues) - 10 > 1 else ''}_",
                    },
                }
            )

        # Prepare Slack payload
        payload = {
            "username": slack_config.get("username", "GitHub Monitor"),
            "icon_emoji": slack_config.get("iconEmoji", ":mag:"),
            "blocks": blocks,
        }

        # Add channel if specified
        if channel := slack_config.get("channel"):
            payload["channel"] = channel

        try:
            response = requests.post(webhook_url, json=payload, timeout=10)
            response.raise_for_status()
            print(f"✅ Slack notification sent for {count} issues")
        except requests.exceptions.RequestException as e:
            print(f"❌ Failed to send Slack notification: {e}")

    def save_new_issues(self, issues: List[Dict[str, Any]]):
        """Save new issues to JSON file for GitHub Actions to process."""
        if issues:
            with open("new_issues.json", "w") as f:
                json.dump(issues, f, indent=2)
            print(f"💾 Saved {len(issues)} new issues to new_issues.json")

    def run(self):
        """Main execution method."""
        try:
            print(f"🔍 Starting issue monitor for: {self.config['name']}")

            # Load cache and search for issues
            cache = self.load_cache()
            issues = self.search_issues()

            print(f"📊 Found {len(issues)} total issues")

            # Debug: Log config before filtering
            print(
                f"[DEBUG] Config filterNonEnglish: "
                f"{self.config.get('filterNonEnglish', 'NOT SET')}",
                flush=True,
            )
            print(f"[DEBUG] Starting to filter {len(issues)} issues...", flush=True)

            # Filter new issues
            new_issues = [
                issue
                for issue in issues
                if issue["id"] not in cache["notified_issues"]
                and not self.is_excluded(issue)
                and not self.is_non_english(issue)
            ]

            print(f"🆕 {len(new_issues)} new issues to notify about")

            if new_issues:
                # Send notifications
                self.send_slack_notification(new_issues)

                # Save new issues for GitHub Actions to process
                # (GitHub Issues)
                github_issues_config = self.config.get("notifications", {}).get(
                    "githubIssues", {}
                )
                if github_issues_config.get(
                    "enabled", True
                ):  # Default to enabled for backward compatibility
                    self.save_new_issues(new_issues)

                # Update cache
                cache["notified_issues"].extend(issue["id"] for issue in new_issues)

                # Keep cache size manageable
                if len(cache["notified_issues"]) > 1000:
                    cache["notified_issues"] = cache["notified_issues"][-1000:]

                self.save_cache(cache)

            print("✅ Monitor run completed successfully")

        except Exception as e:
            print(f"❌ Monitor run failed: {e}")
            raise


def main():
    """Main entry point."""
    config_file = os.getenv("CONFIG_FILE", "configs/template.json.example")

    try:
        with open(config_file, "r") as f:
            config = json.load(f)

        monitor = GitHubIssueMonitor(config)
        monitor.run()

    except FileNotFoundError:
        print(f"❌ Config file not found: {config_file}")
        exit(1)
    except json.JSONDecodeError as e:
        print(f"❌ Invalid JSON in config file: {e}")
        exit(1)
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        exit(1)


if __name__ == "__main__":
    main()
