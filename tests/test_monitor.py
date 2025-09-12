#!/usr/bin/env python3

import json
import os
import tempfile
import unittest
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import Mock, patch, mock_open, MagicMock

import pytest
import requests

# Add src to path for imports
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from monitor_github_notify import GitHubIssueMonitor


class TestGitHubIssueMonitor(unittest.TestCase):

    def setUp(self):
        """Set up test fixtures."""
        self.test_config = {
            "name": "test-monitor",
            "searchPhrases": ["security vulnerability", "critical bug"],
            "excludedRepos": ["spam/repo", "test/exclude"],
            "excludedOrgs": ["spamorg", "excludeorg"],
            "lookbackHours": 24,
            "notifications": {
                "githubIssues": {"enabled": True},
                "slack": {
                    "enabled": True,
                    "channel": "#test-alerts",
                    "webhookUrl": "https://hooks.slack.com/test"
                }
            }
        }

        self.sample_issues = [
            {
                "id": 12345,
                "title": "Critical security vulnerability found",
                "html_url": "https://github.com/owner/repo/issues/123",
                "repository": "owner/repo",
                "user": "reporter1",
                "created_at": "2024-01-15T14:30:00Z",
                "body": "This is a detailed description of the security issue..."
            },
            {
                "id": 67890,
                "title": "Another critical bug",
                "html_url": "https://github.com/another/repo/issues/456",
                "repository": "another/repo",
                "user": "reporter2",
                "created_at": "2024-01-15T15:45:00Z",
                "body": "Bug description here"
            }
        ]

    @patch.dict(os.environ, {'GITHUB_TOKEN': 'fake_token'})
    def test_init(self):
        """Test monitor initialization."""
        monitor = GitHubIssueMonitor(self.test_config)

        self.assertEqual(monitor.config, self.test_config)
        self.assertTrue(monitor.cache_file.name.endswith('test-monitor-cache.json'))
        self.assertIsNotNone(monitor.github)

    def test_build_search_query_basic(self):
        """Test basic search query construction."""
        with patch.dict(os.environ, {'GITHUB_TOKEN': 'fake_token'}):
            monitor = GitHubIssueMonitor(self.test_config)

        with patch('monitor_github_notify.datetime') as mock_datetime:
            mock_datetime.now.return_value = datetime(2024, 1, 15, 12, 0, 0)
            query = monitor.build_search_query()

        expected_phrases = '("security vulnerability" OR "critical bug")'
        self.assertIn(expected_phrases, query)
        self.assertIn('type:issue', query)
        self.assertIn('created:>=2024-01-14', query)  # 24 hours ago

    def test_build_search_query_with_exclusions(self):
        """Test search query with repository and organization exclusions."""
        with patch.dict(os.environ, {'GITHUB_TOKEN': 'fake_token'}):
            monitor = GitHubIssueMonitor(self.test_config)

        with patch('monitor_github_notify.datetime') as mock_datetime:
            mock_datetime.now.return_value = datetime(2024, 1, 15, 12, 0, 0)
            query = monitor.build_search_query()

        self.assertIn('-repo:spam/repo', query)
        self.assertIn('-repo:test/exclude', query)
        self.assertIn('-org:spamorg', query)
        self.assertIn('-org:excludeorg', query)

    def test_build_search_query_custom_lookback(self):
        """Test search query with custom lookback hours."""
        config = self.test_config.copy()
        config['lookbackHours'] = 48

        with patch.dict(os.environ, {'GITHUB_TOKEN': 'fake_token'}):
            monitor = GitHubIssueMonitor(config)

        with patch('monitor_github_notify.datetime') as mock_datetime:
            mock_datetime.now.return_value = datetime(2024, 1, 15, 12, 0, 0)
            query = monitor.build_search_query()

        self.assertIn('created:>=2024-01-13', query)  # 48 hours ago

    def test_is_excluded_repo(self):
        """Test repository exclusion logic."""
        with patch.dict(os.environ, {'GITHUB_TOKEN': 'fake_token'}):
            monitor = GitHubIssueMonitor(self.test_config)

        # Test excluded repo
        excluded_issue = {"repository": "spam/repo"}
        self.assertTrue(monitor.is_excluded(excluded_issue))

        # Test non-excluded repo
        normal_issue = {"repository": "normal/repo"}
        self.assertFalse(monitor.is_excluded(normal_issue))

    def test_is_excluded_org(self):
        """Test organization exclusion logic."""
        with patch.dict(os.environ, {'GITHUB_TOKEN': 'fake_token'}):
            monitor = GitHubIssueMonitor(self.test_config)

        # Test excluded org
        excluded_issue = {"repository": "spamorg/somerepo"}
        self.assertTrue(monitor.is_excluded(excluded_issue))

        # Test non-excluded org
        normal_issue = {"repository": "normalorg/repo"}
        self.assertFalse(monitor.is_excluded(normal_issue))

    def test_load_cache_existing(self):
        """Test loading existing cache file."""
        cache_data = {"notified_issues": [123, 456, 789]}

        with patch.dict(os.environ, {'GITHUB_TOKEN': 'fake_token'}):
            monitor = GitHubIssueMonitor(self.test_config)

        with patch('pathlib.Path.exists', return_value=True), \
             patch('builtins.open', mock_open(read_data=json.dumps(cache_data))):

            result = monitor.load_cache()
            self.assertEqual(result, cache_data)

    def test_load_cache_missing(self):
        """Test loading cache when file doesn't exist."""
        with patch.dict(os.environ, {'GITHUB_TOKEN': 'fake_token'}):
            monitor = GitHubIssueMonitor(self.test_config)

        with patch('pathlib.Path.exists', return_value=False):
            result = monitor.load_cache()
            self.assertEqual(result, {"notified_issues": []})

    def test_load_cache_invalid_json(self):
        """Test loading cache with invalid JSON."""
        with patch.dict(os.environ, {'GITHUB_TOKEN': 'fake_token'}):
            monitor = GitHubIssueMonitor(self.test_config)

        with patch('pathlib.Path.exists', return_value=True), \
             patch('builtins.open', mock_open(read_data="invalid json")):

            result = monitor.load_cache()
            self.assertEqual(result, {"notified_issues": []})

    def test_save_cache(self):
        """Test saving cache to file."""
        cache_data = {"notified_issues": [123, 456]}

        with patch.dict(os.environ, {'GITHUB_TOKEN': 'fake_token'}):
            monitor = GitHubIssueMonitor(self.test_config)

        with patch('pathlib.Path.mkdir') as mock_mkdir, \
             patch('builtins.open', mock_open()) as mock_file:

            monitor.save_cache(cache_data)

            mock_mkdir.assert_called_once_with(parents=True, exist_ok=True)
            mock_file.assert_called_once()

            # Check that json.dump was called with correct data
            written_content = mock_file().write.call_args_list
            written_data = ''.join(call[0][0] for call in written_content)
            self.assertIn('"notified_issues"', written_data)

    @patch('monitor_github_notify.requests.post')
    def test_send_slack_notification_success(self, mock_post):
        """Test successful Slack notification sending."""
        mock_post.return_value.raise_for_status.return_value = None

        with patch.dict(os.environ, {'GITHUB_TOKEN': 'fake_token'}):
            monitor = GitHubIssueMonitor(self.test_config)

        monitor.send_slack_notification(self.sample_issues)

        mock_post.assert_called_once()
        call_args = mock_post.call_args

        # Verify webhook URL
        self.assertEqual(call_args[0][0], "https://hooks.slack.com/test")

        # Verify payload structure
        payload = call_args[1]['json']
        self.assertIn('blocks', payload)
        self.assertEqual(payload['username'], 'GitHub Monitor')

    @patch('monitor_github_notify.requests.post')
    def test_send_slack_notification_disabled(self, mock_post):
        """Test Slack notification when disabled."""
        config = self.test_config.copy()
        config['notifications']['slack']['enabled'] = False

        with patch.dict(os.environ, {'GITHUB_TOKEN': 'fake_token'}):
            monitor = GitHubIssueMonitor(config)

        monitor.send_slack_notification(self.sample_issues)

        mock_post.assert_not_called()

    @patch('monitor_github_notify.requests.post')
    def test_send_slack_notification_error(self, mock_post):
        """Test Slack notification error handling."""
        mock_post.side_effect = requests.exceptions.RequestException("Network error")

        with patch.dict(os.environ, {'GITHUB_TOKEN': 'fake_token'}):
            monitor = GitHubIssueMonitor(self.test_config)

        # Should not raise exception
        monitor.send_slack_notification(self.sample_issues)
        mock_post.assert_called_once()

    def test_save_new_issues(self):
        """Test saving new issues to JSON file."""
        with patch.dict(os.environ, {'GITHUB_TOKEN': 'fake_token'}):
            monitor = GitHubIssueMonitor(self.test_config)

        with patch('builtins.open', mock_open()) as mock_file:
            monitor.save_new_issues(self.sample_issues)

            mock_file.assert_called_once_with('new_issues.json', 'w')

            # Verify JSON content was written
            written_content = mock_file().write.call_args_list
            written_data = ''.join(call[0][0] for call in written_content)
            self.assertIn('"id": 12345', written_data)

    def test_save_new_issues_empty(self):
        """Test saving empty issues list."""
        with patch.dict(os.environ, {'GITHUB_TOKEN': 'fake_token'}):
            monitor = GitHubIssueMonitor(self.test_config)

        with patch('builtins.open', mock_open()) as mock_file:
            monitor.save_new_issues([])

            # Should not create file for empty list
            mock_file.assert_not_called()

    @patch('monitor_github_notify.Github')
    def test_search_issues_success(self, mock_github_class):
        """Test successful issue searching."""
        # Mock GitHub issue object
        mock_issue = Mock()
        mock_issue.id = 12345
        mock_issue.title = "Test Issue"
        mock_issue.html_url = "https://github.com/test/repo/issues/1"
        mock_issue.repository.full_name = "test/repo"
        mock_issue.user.login = "testuser"
        mock_issue.created_at = datetime(2024, 1, 15, 14, 30, 0)
        mock_issue.body = "Test issue body"
        mock_issue.pull_request = None

        mock_github = Mock()
        mock_github.search_issues.return_value = [mock_issue]
        mock_github_class.return_value = mock_github

        with patch.dict(os.environ, {'GITHUB_TOKEN': 'fake_token'}):
            monitor = GitHubIssueMonitor(self.test_config)

        result = monitor.search_issues()

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['id'], 12345)
        self.assertEqual(result[0]['title'], "Test Issue")
        self.assertEqual(result[0]['repository'], "test/repo")

    @patch('monitor_github_notify.Github')
    def test_search_issues_filters_pull_requests(self, mock_github_class):
        """Test that pull requests are filtered out from search results."""
        # Mock GitHub issue (should be included)
        mock_issue = Mock()
        mock_issue.id = 12345
        mock_issue.title = "Test Issue"
        mock_issue.html_url = "https://github.com/test/repo/issues/1"
        mock_issue.repository.full_name = "test/repo"
        mock_issue.user.login = "testuser"
        mock_issue.created_at = datetime(2024, 1, 15, 14, 30, 0)
        mock_issue.body = "Test issue body"
        mock_issue.pull_request = None

        # Mock GitHub pull request (should be excluded)
        mock_pr = Mock()
        mock_pr.id = 67890
        mock_pr.title = "Test PR"
        mock_pr.pull_request = Mock()  # Has pull_request attribute

        mock_github = Mock()
        mock_github.search_issues.return_value = [mock_issue, mock_pr]
        mock_github_class.return_value = mock_github

        with patch.dict(os.environ, {'GITHUB_TOKEN': 'fake_token'}):
            monitor = GitHubIssueMonitor(self.test_config)

        result = monitor.search_issues()

        # Should only return the issue, not the PR
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['id'], 12345)

    @patch('monitor_github_notify.Github')
    def test_search_issues_api_error(self, mock_github_class):
        """Test handling of GitHub API errors."""
        mock_github = Mock()
        mock_github.search_issues.side_effect = Exception("API Error")
        mock_github_class.return_value = mock_github

        with patch.dict(os.environ, {'GITHUB_TOKEN': 'fake_token'}):
            monitor = GitHubIssueMonitor(self.test_config)

        with self.assertRaises(Exception):
            monitor.search_issues()


class TestConfigValidation(unittest.TestCase):
    """Tests for configuration validation."""

    def test_valid_config(self):
        """Test that a valid config loads successfully."""
        config = {
            "name": "test",
            "searchPhrases": ["test"],
            "excludedRepos": [],
            "excludedOrgs": [],
            "lookbackHours": 24,
            "notifications": {
                "githubIssues": {"enabled": True},
                "slack": {"enabled": False}
            }
        }

        with patch.dict(os.environ, {'GITHUB_TOKEN': 'fake_token'}):
            monitor = GitHubIssueMonitor(config)
            self.assertEqual(monitor.config['name'], 'test')

    def test_missing_required_fields(self):
        """Test behavior with missing required configuration fields."""
        incomplete_config = {"name": "test"}

        with patch.dict(os.environ, {'GITHUB_TOKEN': 'fake_token'}):
            monitor = GitHubIssueMonitor(incomplete_config)

            # Should raise KeyError for missing required fields
            with self.assertRaises(KeyError):
                monitor.build_search_query()


if __name__ == '__main__':
    unittest.main()
