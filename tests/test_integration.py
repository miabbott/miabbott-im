#!/usr/bin/env python3

"""Integration tests for the GitHub Issue Monitor."""

import json
import os
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from src.monitor_github_notify import GitHubIssueMonitor, main


class TestIntegration:
    """Integration tests for the complete monitoring workflow."""

    @patch("src.monitor_github_notify.Github")
    @patch("src.monitor_github_notify.requests.post")
    def test_complete_monitoring_workflow(
        self,
        mock_post,
        mock_github_class,
        sample_config,
        sample_issues,
        mock_github_token,
    ):
        """Test the complete monitoring workflow from search to notification."""
        # Setup mocks
        mock_github = Mock()
        mock_github.search_issues.return_value = []  # No issues found initially
        mock_github_class.return_value = mock_github

        # Mock successful Slack response
        mock_post.return_value.raise_for_status.return_value = None

        with tempfile.TemporaryDirectory() as tmpdir:
            # Set cache directory
            monitor = GitHubIssueMonitor(sample_config)
            monitor.cache_file = Path(tmpdir) / "test-cache.json"

            # First run - no issues
            monitor.run()

            # Cache is only created when there are new issues to save
            # For the first run with no issues, cache file won't exist yet

            # Second run - with new issues
            mock_issue1 = Mock()
            mock_issue1.id = 12345
            mock_issue1.title = "Security vulnerability"
            mock_issue1.html_url = "https://github.com/test/repo/issues/1"
            mock_issue1.repository.full_name = "test/repo"
            mock_issue1.user.login = "reporter"
            mock_issue1.created_at.isoformat.return_value = "2024-01-15T14:30:00Z"
            mock_issue1.body = "Critical security issue"
            mock_issue1.pull_request = None

            mock_github.search_issues.return_value = [mock_issue1]

            # Run without mocking file operations so cache can be saved
            monitor.run()

            # Verify Slack notification was sent
            mock_post.assert_called()

            # Verify cache was updated (after processing new issues)
            assert monitor.cache_file.exists()
            cache_data = json.loads(monitor.cache_file.read_text())
            assert 12345 in cache_data["notified_issues"]

    def test_main_function_with_config_file(self, sample_config):
        """Test the main function with a configuration file."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(sample_config, f)
            config_file = f.name

        try:
            with patch.dict(
                os.environ, {"CONFIG_FILE": config_file, "GITHUB_TOKEN": "fake_token"}
            ), patch("src.monitor_github_notify.GitHubIssueMonitor.run") as mock_run:

                main()
                mock_run.assert_called_once()
        finally:
            os.unlink(config_file)

    def test_main_function_missing_config(self):
        """Test main function behavior with missing config file."""
        with patch.dict(
            os.environ,
            {"CONFIG_FILE": "nonexistent.json", "GITHUB_TOKEN": "fake_token"},
        ), pytest.raises(SystemExit) as exc_info:
            main()

        assert exc_info.value.code == 1

    def test_main_function_invalid_json(self):
        """Test main function behavior with invalid JSON config."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            f.write("invalid json content")
            config_file = f.name

        try:
            with patch.dict(
                os.environ, {"CONFIG_FILE": config_file, "GITHUB_TOKEN": "fake_token"}
            ), pytest.raises(SystemExit) as exc_info:
                main()

            assert exc_info.value.code == 1
        finally:
            os.unlink(config_file)

    @patch("src.monitor_github_notify.Github")
    def test_no_new_issues_workflow(
        self, mock_github_class, sample_config, mock_github_token
    ):
        """Test workflow when no new issues are found."""
        mock_github = Mock()
        mock_github.search_issues.return_value = []
        mock_github_class.return_value = mock_github

        with tempfile.TemporaryDirectory() as tmpdir:
            monitor = GitHubIssueMonitor(sample_config)
            monitor.cache_file = Path(tmpdir) / "test-cache.json"

            with patch("src.monitor_github_notify.requests.post") as mock_post, patch(
                "builtins.open", create=True
            ) as mock_open:

                monitor.run()

                # No Slack notification should be sent
                mock_post.assert_not_called()

                # No new_issues.json should be created
                assert not any(
                    "new_issues.json" in str(call) for call in mock_open.call_args_list
                )

    @patch("src.monitor_github_notify.Github")
    def test_duplicate_issue_filtering(
        self, mock_github_class, sample_config, mock_github_token
    ):
        """Test that duplicate issues are properly filtered out."""
        mock_github = Mock()

        # Create mock issue
        mock_issue = Mock()
        mock_issue.id = 12345
        mock_issue.title = "Test Issue"
        mock_issue.html_url = "https://github.com/test/repo/issues/1"
        mock_issue.repository.full_name = "test/repo"
        mock_issue.user.login = "reporter"
        mock_issue.created_at.isoformat.return_value = "2024-01-15T14:30:00Z"
        mock_issue.body = "Test body"
        mock_issue.pull_request = None

        mock_github.search_issues.return_value = [mock_issue]
        mock_github_class.return_value = mock_github

        with tempfile.TemporaryDirectory() as tmpdir:
            monitor = GitHubIssueMonitor(sample_config)
            monitor.cache_file = Path(tmpdir) / "test-cache.json"

            # First run - issue should be processed
            with patch("src.monitor_github_notify.requests.post") as mock_post:
                monitor.run()
                mock_post.assert_called_once()

            # Second run - same issue should be filtered out
            with patch("src.monitor_github_notify.requests.post") as mock_post:
                monitor.run()
                mock_post.assert_not_called()


class TestErrorHandling:
    """Test error handling scenarios."""

    @patch("src.monitor_github_notify.Github")
    def test_github_api_error_handling(
        self, mock_github_class, sample_config, mock_github_token
    ):
        """Test handling of GitHub API errors."""
        mock_github = Mock()
        mock_github.search_issues.side_effect = Exception("GitHub API Error")
        mock_github_class.return_value = mock_github

        monitor = GitHubIssueMonitor(sample_config)

        with pytest.raises(Exception, match="GitHub API Error"):
            monitor.run()

    @patch("src.monitor_github_notify.Github")
    @patch("src.monitor_github_notify.requests.post")
    def test_slack_error_handling(
        self, mock_post, mock_github_class, sample_config, mock_github_token
    ):
        """Test handling of Slack notification errors."""
        # Setup GitHub mock
        mock_github = Mock()
        mock_issue = Mock()
        mock_issue.id = 12345
        mock_issue.title = "Test Issue"
        mock_issue.html_url = "https://github.com/test/repo/issues/1"
        mock_issue.repository.full_name = "test/repo"
        mock_issue.user.login = "reporter"
        mock_issue.created_at.isoformat.return_value = "2024-01-15T14:30:00Z"
        mock_issue.body = "Test body"
        mock_issue.pull_request = None

        mock_github.search_issues.return_value = [mock_issue]
        mock_github_class.return_value = mock_github

        # Slack error
        mock_post.side_effect = Exception("Slack error")

        monitor = GitHubIssueMonitor(sample_config)

        # Should raise exception on Slack error (not handled gracefully currently)
        with patch("builtins.open", create=True):
            with pytest.raises(Exception, match="Slack error"):
                monitor.run()

    def test_cache_permission_error(self, sample_config, mock_github_token):
        """Test handling of cache file permission errors."""
        monitor = GitHubIssueMonitor(sample_config)

        # Mock permission error on cache save
        with patch(
            "pathlib.Path.mkdir", side_effect=PermissionError("Permission denied")
        ):
            cache_data = {"notified_issues": [123]}

            with pytest.raises(PermissionError):
                monitor.save_cache(cache_data)


if __name__ == "__main__":
    pytest.main([__file__])
