# GitHub Issue Monitor (GitHub Issues Notifications)

A template-based GitHub Actions tool for monitoring GitHub issues and creating GitHub issue notifications. **No email credentials required!**

## Features

- 🔍 **Flexible Search**: Monitor issues by search phrases across all of GitHub
- 📋 **GitHub Issue Notifications**: Creates issues in your repo with findings
- 🚫 **Smart Exclusions**: Exclude specific repositories and organizations
- ⚙️ **Template-Based**: Easy to create multiple monitors for different topics
- 🤖 **GitHub Actions**: Runs automatically on schedule using free GitHub Actions
- 💾 **Duplicate Prevention**: Tracks notified issues to prevent spam
- 🔒 **No Credentials**: Uses GitHub's built-in permissions, no email setup needed

## Quick Setup

### 1. Repository Setup

**No email credentials needed!** The tool creates GitHub issues for notifications.

Simply ensure your repository has:
- Issues enabled (Settings → Features → Issues)
- `GITHUB_TOKEN` secret (usually auto-provided by GitHub Actions)

### 2. Create Configuration

Copy `configs/example-template.json` and customize:

```json
{
  "name": "fedora-iot",
  "searchPhrases": [
    "Fedora IoT"
  ],
  "excludedRepos": [
    "spam-owner/test-repo"
  ],
  "excludedOrgs": [
    "spam-organization"
  ],
  "lookbackHours": 24
}
```

### 3. Use the GitHub Issues Workflow

Use `.github/workflows/fedora-iot-monitor-github.yml` which creates GitHub issues for notifications.

## How It Works

1. **Search**: Monitors GitHub for issues matching your phrases
2. **Filter**: Excludes specified repos/orgs and previously notified issues
3. **Notify**: Creates a GitHub issue in your repository with all findings
4. **Subscribe**: Get notifications via GitHub's native notification system

## Notification Format

When new issues are found, a GitHub issue is created like:

```markdown
# 🔍 3 new Fedora IoT issues found - 2024-01-15

Found 3 new GitHub issues matching **"Fedora IoT"**:

## 📋 [Boot failure on Raspberry Pi with Fedora IoT](https://github.com/owner/repo/issues/123)

- **Repository:** `owner/repo`
- **Author:** [@username](https://github.com/username)
- **Created:** 1/15/2024, 2:30:00 PM
- **Link:** https://github.com/owner/repo/issues/123

**Preview:**
> System fails to boot after updating to latest Fedora IoT image...

---

## 📋 [Security vulnerability in IoT image](https://github.com/another/repo/issues/456)

- **Repository:** `another/repo`
- **Author:** [@security-researcher](https://github.com/security-researcher)
- **Created:** 1/15/2024, 3:45:00 PM
- **Link:** https://github.com/another/repo/issues/456

---

*This issue was automatically created by the Fedora IoT monitor on 2024-01-15*
```

## Getting Notifications

You'll automatically get GitHub notifications for new issues created in your repository:

1. **Browser**: GitHub notifications bell icon
2. **Email**: If you have GitHub email notifications enabled
3. **Mobile**: GitHub mobile app notifications
4. **Watch**: You can "watch" your own repository for instant notifications

## Configuration Options

| Field | Description | Example |
|-------|-------------|---------|
| `name` | Unique identifier for this monitor | `"fedora-iot"` |
| `searchPhrases` | Array of phrases to search for | `["Fedora IoT", "security issue"]` |
| `excludedRepos` | Repositories to ignore | `["owner/repo"]` |
| `excludedOrgs` | Organizations to ignore | `["spam-org"]` |
| `lookbackHours` | How far back to search (hours) | `24` |

## Multiple Monitors

You can create multiple monitoring workflows:

1. Create separate config files: `configs/security.json`, `configs/bugs.json`
2. Create separate workflow files: `.github/workflows/security-monitor-github.yml`
3. Each monitor creates issues with different labels for easy filtering

## Testing

Test your configuration manually:

```bash
# Set environment variables
export GITHUB_TOKEN="your_token"
export CONFIG_FILE="configs/fedora-iot.json"

# Install dependencies
pip install -r requirements.txt

# Run monitor (creates new_issues.json if issues found)
python src/monitor_github_notify.py
```

## Advantages Over Email

✅ **No setup required** - works out of the box  
✅ **Free forever** - no external service limits  
✅ **Rich formatting** - markdown, links, previews  
✅ **Searchable** - GitHub's powerful issue search  
✅ **Collaborative** - others can comment and discuss  
✅ **Mobile notifications** - via GitHub mobile app  
✅ **Persistent** - permanent record of all findings  

## Scheduling Options

Common cron schedules:
- `'0 * * * *'` - Every hour
- `'0 */2 * * *'` - Every 2 hours  
- `'0 9,17 * * *'` - 9 AM and 5 PM daily
- `'0 9 * * MON-FRI'` - 9 AM weekdays only

## Labels

Issues are automatically labeled with:
- `fedora-iot-monitor` - Identifies the monitor type
- `notification` - Marks as automated notification
- `auto-created` - Indicates automated creation

## Cost

This tool uses only free services:
- GitHub Actions (2000 minutes/month free)
- GitHub API (5000 requests/hour)
- GitHub Issues (unlimited)

Typical usage: ~2-5 minutes/month for bi-hourly monitoring.