# Fleet Tracker - Automated GitHub Pages Setup

This guide will help you set up automatic daily updates for your Fleet Tracker and host it for free on GitHub Pages.

## What You'll Get

- A live URL like `https://yourusername.github.io/usn/` that anyone can access
- Automatic daily updates at 6:00 AM UTC (adjustable)
- Manual refresh option anytime from GitHub
- Zero hosting costs

---

## Setup Instructions

### Step 1: Push Code to Your GitHub Repository

Make sure all these files are in your repository:
- `fleet_scraper.py` - The scraper script
- `.github/workflows/update-fleet-tracker.yml` - The automation workflow
- `requirements.txt` - Python dependencies

### Step 2: Enable GitHub Pages

1. Go to your repository on GitHub
2. Click **Settings** (tab at the top)
3. Scroll down to **Pages** in the left sidebar
4. Under **Source**, select **GitHub Actions**
5. Click **Save**

### Step 3: Enable GitHub Actions

1. Go to the **Actions** tab in your repository
2. If prompted, click **"I understand my workflows, go ahead and enable them"**
3. You should see the "Update Fleet Tracker" workflow listed

### Step 4: Run Your First Update

1. Go to **Actions** tab
2. Click **"Update Fleet Tracker"** in the left sidebar
3. Click **"Run workflow"** dropdown on the right
4. Click the green **"Run workflow"** button
5. Wait 2-3 minutes for it to complete

### Step 5: Access Your Live Site

Once the workflow completes successfully:
- Your site will be live at: `https://YOUR_USERNAME.github.io/YOUR_REPO_NAME/`
- Example: `https://ianellisjones.github.io/usn/`

---

## Configuration Options

### Change Update Schedule

Edit `.github/workflows/update-fleet-tracker.yml` and modify the cron schedule:

```yaml
schedule:
  - cron: '0 6 * * *'  # Currently: 6:00 AM UTC daily
```

Common schedules:
- `'0 6 * * *'` - Daily at 6:00 AM UTC
- `'0 */6 * * *'` - Every 6 hours
- `'0 6,18 * * *'` - Twice daily (6 AM and 6 PM UTC)
- `'0 6 * * 1'` - Weekly on Mondays at 6 AM UTC

### Manual Updates

You can trigger an update anytime:
1. Go to **Actions** tab
2. Select **"Update Fleet Tracker"**
3. Click **"Run workflow"**

---

## Troubleshooting

### Workflow Failed?

1. Go to **Actions** tab
2. Click on the failed run
3. Click on the failed job to see logs
4. Common issues:
   - Network timeout (USCarriers.net was slow) - just re-run
   - Python error - check the scraper logs

### Site Not Updating?

1. Check that GitHub Pages is set to deploy from **GitHub Actions** (not a branch)
2. Make sure the workflow completed successfully (green checkmark)
3. Try a hard refresh in your browser (Ctrl+Shift+R)

### Want to Test Locally?

```bash
pip install requests beautifulsoup4
python fleet_scraper.py
# Opens index.html in your browser
```

---

## Sharing with Subscribers

Simply share your GitHub Pages URL:

```
https://YOUR_USERNAME.github.io/YOUR_REPO_NAME/
```

The page:
- Works on desktop and mobile
- Requires no login or installation
- Updates automatically every day
- Is completely free to host

---

## Files Overview

| File | Purpose |
|------|---------|
| `fleet_scraper.py` | Scrapes USCarriers.net and generates HTML |
| `index.html` | The generated tracker (auto-updated) |
| `.github/workflows/update-fleet-tracker.yml` | GitHub Actions automation |
| `requirements.txt` | Python dependencies |
| `Big_Deck_Fleet_Globe.ipynb` | Original Colab notebook (optional) |

---

## Support

- Data Source: [USCarriers.net](http://uscarriers.net)
- For issues with this tracker, check the Actions logs
