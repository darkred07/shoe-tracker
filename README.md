# 👟 Shoe Price Tracker

An intelligent shoe price tracker that uses Google's Gemini API to extract prices from product pages and alerts you when prices drop below your threshold.

## 🚀 Features

- **AI-Powered Price Extraction**: Uses Gemini API to intelligently parse any e-commerce site
- **Email Alerts**: Get notified via Amazon SES when prices drop below your threshold
- **Threshold Alerts**: Set global or per-URL price thresholds
- **Price History**: Tracks price changes over time
- **Daily Automation**: Set up automated daily checks via cron
- **Multi-Site Support**: Works with Nike, Adidas, Amazon, and more

## 📋 Prerequisites

- Python 3.8 or higher
- Google Gemini API key ([Get one free here](https://makersuite.google.com/app/apikey))

## 🔧 Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure API Key

Create a `.env` file in the project directory:

```bash
cp .env.example .env
```

Edit `.env` and add your Gemini API key:

```
GEMINI_API_KEY=your_actual_api_key_here
```

### 3. Configure Email Notifications (Optional)

To receive email alerts via Amazon SES when products drop below threshold:

1. **Set up Amazon SES:**
   - Go to [AWS SES Console](https://console.aws.amazon.com/ses/)
   - Verify your "from" email address (Settings → Verified identities)
   - If in sandbox mode, also verify recipient email addresses
   - Create AWS access credentials ([IAM Console](https://console.aws.amazon.com/iam/))

2. **Add to `.env` file:**
```bash
# Amazon SES Configuration
AWS_ACCESS_KEY_ID=your_aws_access_key_id
AWS_SECRET_ACCESS_KEY=your_aws_secret_access_key
AWS_REGION=us-east-1

# Email Configuration
EMAIL_FROM=your-verified-email@example.com
EMAIL_TO=recipient@example.com
```

**Notes:**
- `EMAIL_FROM` must be verified in SES
- `EMAIL_TO` can be comma-separated for multiple recipients
- If not configured, the script will still work but won't send emails

### 4. Add URLs to Track

Edit `tracked_urls.json` and add your shoe URLs:

```json
{
  "settings": {
    "model": "gemini-flash-latest",
    "threshold": 50000,
    "shoe_names": ["Forum", "Samba", "Rivalry"]
  },
  "urls": [
    {
      "name": "Adidas Shoes - Woker Sporting",
      "url": "https://www.wokerbysporting.com.ar/...",
      "selector": "#gallery-layout-container"
    },
    {
      "name": "Nike Shoes - Another Store",
      "url": "https://example.com/nike",
      "threshold": 100000,
      "selector": ".product-grid"
    }
  ]
}
```

**Settings:**
- `model`: Gemini model to use (e.g., `gemini-flash-latest`, `gemini-2.5-pro`)
- `threshold`: Default price threshold for all URLs (can be overridden per URL)
- `shoe_names`: (Optional) Array of shoe model keywords to filter notifications. Only products containing these keywords (case-insensitive) will trigger alerts. Leave empty `[]` or omit to get alerts for all shoes below threshold.
  - Example: `["Forum", "Samba", "Rivalry"]` will only alert for shoes with these names

**URL Fields:**
- `name`: Product description (for your reference)
- `url`: Full product listing/search page URL
- `threshold`: (Optional) Override the default threshold for this specific URL
- `selector`: (Optional) CSS selector for product container (e.g., `#gallery-layout-container`, `.product-grid`)
  - If not provided, uses entire page body
  - Use browser DevTools to find the container that wraps product listings

## 🏃 Usage

### Run Manual Check

```bash
python shoe_price_tracker.py
```

### Output Example

```
============================================================
🏃 Starting price check at 2025-11-26 00:30:00
============================================================

🔍 Checking: Nike Air Max 90 White
   URL: https://www.nike.com/...
   💰 Current price: $95.00
   🎯 Threshold: $100.00
   🚨 ALERT! Price is at or below threshold!
   💸 Current: $95.00 | Threshold: $100.00
   🛒 Buy now: https://www.nike.com/...

============================================================
📊 SUMMARY
============================================================
✅ Checked: 1/1 items

🚨 1 PRICE ALERT(S)!
   • Nike Air Max 90 White: $95.00 (threshold: $100.00)
     https://www.nike.com/...
============================================================
```

## ⏰ Automated Daily Checks

### Option 1: Using Cron (macOS/Linux)

1. Make the run script executable:
```bash
chmod +x run_daily_check.sh
```

2. Edit your crontab:
```bash
crontab -e
```

3. Add this line to run daily at 9 AM:
```
0 9 * * * cd /Users/rodrigograna/Documents/IM/Scripts/shoe-tracker && ./run_daily_check.sh
```

### Option 2: Using launchd (macOS)

Create a launch agent (more reliable on macOS than cron):

1. Create `~/Library/LaunchAgents/com.user.shoetracker.plist`:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.user.shoetracker</string>
    <key>ProgramArguments</key>
    <array>
        <string>/usr/bin/python3</string>
        <string>/Users/rodrigograna/Documents/IM/Scripts/shoe-tracker/shoe_price_tracker.py</string>
    </array>
    <key>StartCalendarInterval</key>
    <dict>
        <key>Hour</key>
        <integer>9</integer>
        <key>Minute</key>
        <integer>0</integer>
    </dict>
    <key>WorkingDirectory</key>
    <string>/Users/rodrigograna/Documents/IM/Scripts/shoe-tracker</string>
    <key>StandardOutPath</key>
    <string>/Users/rodrigograna/Documents/IM/Scripts/shoe-tracker/logs/output.log</string>
    <key>StandardErrorPath</key>
    <string>/Users/rodrigograna/Documents/IM/Scripts/shoe-tracker/logs/error.log</string>
</dict>
</plist>
```

2. Load the agent:
```bash
launchctl load ~/Library/LaunchAgents/com.user.shoetracker.plist
```

## 📁 Files

- `shoe_price_tracker.py` - Main tracker script
- `tracked_urls.json` - URLs and thresholds configuration
- `price_history.json` - Historical price data (auto-generated)
- `.env` - API key configuration
- `requirements.txt` - Python dependencies
- `run_daily_check.sh` - Shell script for automation

## 🔍 Troubleshooting

### "GEMINI_API_KEY not found"
Make sure you created a `.env` file with your API key.

### "Could not extract price"
- Check that the URL is accessible
- Some sites may block automated requests - try accessing the URL in a browser first
- The HTML structure might be complex - Gemini will try its best but some sites are tricky

### Price seems wrong
Check `price_history.json` to see the extraction history. You may need to adjust the URL or product name.

## 📝 Notes

- The script keeps the last 30 price checks in history
- Gemini API has generous free tier limits (60 requests/minute)
- **Rate limiting**: The script automatically waits 30 seconds between URL checks to ensure max 2 URLs per minute
- Price history is stored locally in `price_history.json`

## 🤝 Contributing

Feel free to customize the script for your needs!

## 📄 License

MIT License - feel free to use and modify as needed.
