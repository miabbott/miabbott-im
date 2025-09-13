# GitHub Issue Monitor (GitHub Issues Notifications)

A template-based GitHub Actions tool for monitoring GitHub issues and creating GitHub issue notifications.

## Features

- 🔍 **Flexible Search**: Monitor issues by search phrases across all of GitHub
- 📋 **GitHub Issue Notifications**: Creates issues in your repo with findings
- 💬 **Slack Integration**: Optional real-time Slack notifications ([setup guide](docs/slack-setup.md))
- 🚫 **Smart Exclusions**: Exclude specific repositories and organizations
- ⚙️ **Template-Based**: Easy to create multiple monitors for different topics
- 🤖 **GitHub Actions**: Runs automatically on schedule using free GitHub Actions
- 💾 **Duplicate Prevention**: Tracks notified issues to prevent spam
- 🔒 **No Credentials**: Uses GitHub's built-in permissions, no email setup needed

## Quick Setup

### 1. Repository Setup

The tool creates GitHub issues for notifications.

Simply ensure your repository has:
- Issues enabled (Settings → Features → Issues)
- `GITHUB_TOKEN` secret (usually auto-provided by GitHub Actions)

### 2. Create Your First Monitor

Copy `configs/template.json.example` to create your own monitor (e.g., `configs/my-monitor.json`):

```json
{
  "name": "my-security-monitor",
  "description": "Monitor for security-related issues",
  "enabled": true,
  "searchPhrases": [
    "security vulnerability",
    "critical bug",
    "CVE-"
  ],
  "excludedRepos": [
    "spam-owner/test-repo"
  ],
  "excludedOrgs": [
    "spam-organization"
  ],
  "lookbackHours": 24,
  "notifications": {
    "githubIssues": {
      "enabled": true
    },
    "slack": {
      "enabled": false,
      "channel": "#alerts"
    }
  }
}
```

### 3. Automatic Workflow Execution

The universal GitHub Actions workflow (`.github/workflows/monitors.yml`) automatically:
- **Discovers** all JSON config files in `configs/` directory
- **Runs** each enabled monitor in parallel
- **Creates** GitHub issues with findings from each monitor
- **Schedules** execution every 2 hours (or run manually)

## How It Works

1. **Search**: Monitors GitHub for issues matching your phrases
2. **Filter**: Excludes specified repos/orgs and previously notified issues
3. **Notify**: Creates a GitHub issue in your repository with all findings
4. **Subscribe**: Get notifications via GitHub's native notification system

## Notification Format

When new issues are found, a GitHub issue is created like:

```markdown
# 🔍 [security-monitor] 3 new issues found - 2024-01-15

Found 3 new GitHub issues matching keywords:

**Monitor:** `security-monitor`
**Config:** `configs/security-monitor.json`

---

## 📋 [Critical security vulnerability in authentication](https://github.com/owner/repo/issues/123)

- **Repository:** `owner/repo`
- **Author:** [@username](https://github.com/username)
- **Created:** 1/15/2024, 2:30:00 PM
- **Link:** https://github.com/owner/repo/issues/123

**Preview:**
> Found a critical security vulnerability that allows unauthorized access...

---

## 📋 [Security vulnerability in API endpoint](https://github.com/another/repo/issues/456)

- **Repository:** `another/repo`
- **Author:** [@security-researcher](https://github.com/security-researcher)
- **Created:** 1/15/2024, 3:45:00 PM
- **Link:** https://github.com/another/repo/issues/456

---

*This issue was automatically created by the GitHub issue monitor (`security-monitor`) on 2024-01-15*
```

**Enhanced Features:**
- Monitor name in title and labels for easy identification
- Config file reference for traceability
- Unique labels per monitor: `monitor-security-monitor`, `github-monitor`, etc.

## Getting Notifications

You'll automatically get GitHub notifications for new issues created in your repository:

1. **Browser**: GitHub notifications bell icon
2. **Email**: If you have GitHub email notifications enabled
3. **Mobile**: GitHub mobile app notifications
4. **Watch**: You can "watch" your own repository for instant notifications

## Configuration Options

| Field | Description | Example |
|-------|-------------|---------|
| `name` | Unique identifier for this monitor | `"security-monitor"` |
| `description` | Human-readable description | `"Monitor for security issues"` |
| `enabled` | Whether this monitor is active | `true` |
| `version` | Config version for tracking changes | `"1.0"` |
| `searchPhrases` | Array of phrases to search for | `["security vulnerability", "critical bug"]` |
| `excludedRepos` | Repositories to ignore | `["owner/repo"]` |
| `excludedOrgs` | Organizations to ignore | `["spam-org"]` |
| `lookbackHours` | How far back to search (hours) | `24` |
| `notifications.githubIssues.enabled` | Enable GitHub issue creation | `true` |
| `notifications.slack.enabled` | Enable Slack notifications | `false` |
| `notifications.slack.channel` | Slack channel for notifications | `"#alerts"` |
| `metadata.tags` | Tags for organization | `["security", "high-priority"]` |

**For Slack setup**, see the [detailed Slack integration guide](docs/slack-setup.md).

## Multiple Monitors

Creating multiple monitors is simple - just add more JSON config files:

```bash
configs/
├── security-monitor.json          # Security vulnerabilities
├── bug-monitor.json              # Critical bugs
├── feature-request-monitor.json  # Feature requests
└── template.json.example         # Template (ignored by workflow)
```

**Key Benefits:**
- ✅ **No separate workflow files needed** - one workflow runs them all
- ✅ **Automatic discovery** - new configs are detected automatically
- ✅ **Parallel execution** - monitors run simultaneously for faster results
- ✅ **Individual control** - enable/disable monitors with the `enabled` field
- ✅ **Unique labeling** - each monitor gets its own GitHub issue labels

**Example monitors:**
- **Security**: `configs/security-monitor.json` - CVEs, vulnerabilities
- **Bugs**: `configs/bug-monitor.json` - critical bugs, crashes
- **Features**: `configs/feature-requests.json` - enhancement requests

Each monitor creates GitHub issues with distinct labels like `monitor-security-monitor` for easy filtering.

## Testing

Test your configuration manually:

```bash
# Set environment variables
export GITHUB_TOKEN="your_token"
export CONFIG_FILE="configs/your-monitor.json"  # Point to your config

# Install dependencies
pip install -r requirements.txt

# Run monitor (creates new_issues.json if issues found)
python src/monitor_github_notify.py
```

**Test the full workflow locally:**
```bash
# Test workflow config discovery
find configs/ -name "*.json" -not -name "*template*" -not -name "*example*"

# Test individual monitor
export CONFIG_FILE="configs/security-monitor.json"
python src/monitor_github_notify.py

# Run with manual trigger (GitHub CLI required)
gh workflow run monitors.yml
```


## Scheduling Options

Common cron schedules:
- `'0 * * * *'` - Every hour
- `'0 */2 * * *'` - Every 2 hours
- `'0 9,17 * * *'` - 9 AM and 5 PM daily
- `'0 9 * * MON-FRI'` - 9 AM weekdays only

## Labels

Issues are automatically labeled with:
- `github-monitor` - Identifies the monitor type
- `notification` - Marks as automated notification
- `auto-created` - Indicates automated creation

## Cost

This tool uses only free services:
- GitHub Actions (2000 minutes/month free)
- GitHub API (5000 requests/hour)
- GitHub Issues (unlimited)

Typical usage: ~2-5 minutes/month for bi-hourly monitoring.