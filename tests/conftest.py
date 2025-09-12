"""Pytest configuration and shared fixtures."""

import json
import os
import tempfile
from pathlib import Path
from unittest.mock import Mock
import pytest


@pytest.fixture
def sample_config():
    """Sample configuration for testing."""
    return {
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
                "webhookUrl": "https://hooks.slack.com/test",
                "username": "Test Monitor",
                "iconEmoji": ":test:"
            }
        }
    }


@pytest.fixture
def sample_issues():
    """Sample GitHub issues for testing."""
    return [
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


@pytest.fixture
def mock_github_token():
    """Mock GitHub token environment variable."""
    with pytest.MonkeyPatch.context() as m:
        m.setenv("GITHUB_TOKEN", "fake_token_for_testing")
        yield "fake_token_for_testing"


@pytest.fixture
def temp_cache_dir():
    """Temporary directory for cache files during testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def mock_github_issue():
    """Mock GitHub issue object for testing."""
    issue = Mock()
    issue.id = 12345
    issue.title = "Test Issue"
    issue.html_url = "https://github.com/test/repo/issues/1"
    issue.repository.full_name = "test/repo"
    issue.user.login = "testuser"
    issue.created_at.isoformat.return_value = "2024-01-15T14:30:00Z"
    issue.body = "Test issue body"
    issue.pull_request = None
    return issue
