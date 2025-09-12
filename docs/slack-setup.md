# Slack Integration Setup

This guide shows how to set up Slack notifications for your GitHub issue monitor.

## Quick Setup

1. **Create Slack App & Webhook**
2. **Configure your monitor**  
3. **Add webhook URL to GitHub secrets**
4. **Test the integration**

## Step 1: Create Slack Incoming Webhook

### Option A: Simple Incoming Webhooks (Recommended)

1. Go to https://api.slack.com/messaging/webhooks
2. Click **"Create your Slack app"**
3. Choose **"From scratch"**
4. Name your app (e.g., "GitHub Issue Monitor")
5. Select your workspace
6. Go to **"Incoming Webhooks"** in the sidebar
7. Toggle **"Activate Incoming Webhooks"** to On
8. Click **"Add New Webhook to Workspace"**
9. Choose the channel where you want notifications
10. Copy the webhook URL (starts with `https://hooks.slack.com/`)

### Option B: Full Slack App (Advanced)

1. Go to https://api.slack.com/apps
2. Click **"Create New App"** → **"From scratch"**
3. Name your app and select workspace
4. Go to **"Incoming Webhooks"** and enable them
5. Add webhook to workspace and select channel
6. Copy the webhook URL

## Step 2: Configure Your Monitor

Edit your config file (e.g., `configs/fedora-iot.json`):

```json
{
  "name": "fedora-iot",
  "searchPhrases": ["Fedora IoT"],
  "excludedRepos": [],
  "excludedOrgs": [],
  "lookbackHours": 24,
  "notifications": {
    "githubIssues": {
      "enabled": true
    },
    "slack": {
      "enabled": true,
      "webhookUrl": "",
      "channel": "#fedora-iot-alerts", 
      "username": "GitHub Monitor",
      "iconEmoji": ":mag:"
    }
  }
}
```

**Configuration Options:**

| Field | Description | Example |
|-------|-------------|---------|
| `enabled` | Enable/disable Slack notifications | `true` |
| `webhookUrl` | Webhook URL (can be left empty, use secret instead) | `""` |
| `channel` | Target channel (optional, overrides webhook default) | `"#alerts"` |
| `username` | Bot display name | `"GitHub Monitor"` |
| `iconEmoji` | Bot icon emoji | `":mag:"` |

## Step 3: Add Webhook to GitHub Secrets

1. Go to your GitHub repository
2. Navigate to **Settings** → **Secrets and variables** → **Actions**
3. Click **"New repository secret"**
4. Name: `SLACK_WEBHOOK_URL`
5. Value: Your webhook URL from Step 1
6. Click **"Add secret"**

## Step 4: Test the Integration

### Manual Test

```bash
# Set environment variables
export GITHUB_TOKEN="your_github_token"
export SLACK_WEBHOOK_URL="your_webhook_url"
export CONFIG_FILE="configs/fedora-iot.json"

# Run the monitor
python src/monitor_github_notify.py
```

### Workflow Test

1. Go to **Actions** tab in your repository
2. Select your monitor workflow
3. Click **"Run workflow"** to trigger manually
4. Check your Slack channel for notifications

## Notification Format

Slack notifications include:

- **Header**: Number of issues found
- **Summary**: Search phrases matched
- **Issue blocks** (up to 10):
  - Clickable issue title
  - Repository link
  - Author link  
  - Creation date
  - "View Issue" button
- **Overflow indicator** if more than 10 issues

## Multiple Notification Types

You can enable both GitHub Issues and Slack notifications:

```json
{
  "notifications": {
    "githubIssues": {
      "enabled": true
    },
    "slack": {
      "enabled": true,
      "channel": "#alerts"
    }
  }
}
```

This gives you:
- ✅ **GitHub Issues**: Permanent, searchable record
- ✅ **Slack**: Real-time team notifications

## Troubleshooting

### No Slack Messages Sent

1. **Check webhook URL**: Verify the `SLACK_WEBHOOK_URL` secret is correct
2. **Check configuration**: Ensure `slack.enabled: true` in your config
3. **Check permissions**: Verify the Slack app has permission to post to the channel
4. **Check logs**: Look for error messages in GitHub Actions logs

### Slack Says "Webhook URL Not Found"

- The webhook URL is invalid or expired
- Regenerate the webhook URL in your Slack app settings

### Messages Going to Wrong Channel

- The `channel` setting in config overrides the webhook's default channel
- Remove the `channel` field to use the webhook's default
- Or update the channel name (must start with `#`)

### Rate Limiting

- Slack allows ~1 message per second
- The monitor batches all findings into a single message to avoid limits

## Security Notes

- ✅ Webhook URLs are treated as secrets (don't commit them to git)
- ✅ Use GitHub repository secrets to store webhook URLs
- ✅ Webhook URLs can be regenerated if compromised
- ✅ Slack apps can be limited to specific channels

## Channel Recommendations

Consider creating dedicated channels:
- `#github-alerts` - General GitHub notifications
- `#security-alerts` - Security-related issues  
- `#fedora-iot` - Fedora IoT specific issues
- `#bot-notifications` - All automated notifications