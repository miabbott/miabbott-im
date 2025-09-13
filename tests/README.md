# Tests for GitHub Issue Monitor

This directory contains comprehensive tests for the GitHub issue monitoring tool.

## Running Tests

### Install Test Dependencies
```bash
pip install -r tests/requirements-test.txt
```

### Run All Tests
```bash
# Run all tests with coverage
pytest

# Run specific test file
pytest tests/test_monitor.py

# Run with verbose output
pytest -v

# Run only unit tests
pytest tests/test_monitor.py

# Run only integration tests
pytest tests/test_integration.py
```

### Test Coverage
```bash
# Generate coverage report
pytest --cov=src --cov-report=html

# View coverage report
open htmlcov/index.html
```

## Test Structure

### `test_monitor.py`
Unit tests for the core `GitHubIssueMonitor` class:
- Configuration handling
- Search query building
- Issue filtering logic
- Cache operations
- Slack notification formatting
- GitHub API interactions (mocked)

### `test_integration.py`
Integration tests for complete workflows:
- End-to-end monitoring process
- Error handling scenarios
- File I/O operations
- Multiple notification types

### `conftest.py`
Shared test fixtures and configuration:
- Sample configurations
- Mock GitHub issues
- Temporary directories
- Common test utilities

## Test Categories

### ✅ **Unit Tests**
- Fast, isolated tests for individual methods
- Heavy use of mocking for external dependencies
- Focus on business logic and edge cases

### 🔗 **Integration Tests**
- Test complete workflows and interactions
- File system operations with temporary directories
- Error handling and resilience testing

### 🛡️ **Security Tests**
- Token handling
- Input validation
- Error message sanitization

## Mocking Strategy

External dependencies are mocked:
- **GitHub API** (`github.Github`) - Prevents API calls during testing
- **Slack Webhooks** (`requests.post`) - Avoids external HTTP requests
- **File System** - Uses temporary directories for cache files
- **Environment Variables** - Controlled test environment

## Coverage Goals

- **Minimum Coverage**: 80%
- **Target Coverage**: 90%+
- **Critical Paths**: 100% (cache operations, API calls, error handling)

## Common Test Patterns

### Testing Configuration
```python
def test_config_validation():
    config = {"name": "test", "searchPhrases": ["test"]}
    monitor = GitHubIssueMonitor(config)
    assert monitor.config["name"] == "test"
```

### Testing with Mocks
```python
@patch('src.monitor_github_notify.requests.post')
def test_slack_notification(mock_post):
    mock_post.return_value.raise_for_status.return_value = None
    # Test Slack notification logic
```

### Testing Error Handling
```python
def test_api_error_handling():
    with pytest.raises(Exception):
        # Test that errors are properly handled
```

## Continuous Integration

These tests are designed to run in CI environments:
- No external API dependencies
- Deterministic results
- Fast execution (<30 seconds)
- Clear error reporting
