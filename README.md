# cautious-system

## News email task

This repository now includes a task script (`news_email_task.py`) that sends you an email whenever it sees new headlines.

### 1) Get required values

- `NEWS_API_KEY`: API key from [NewsAPI](https://newsapi.org/)
- `SMTP_HOST`: SMTP server host (e.g., `smtp.gmail.com`)
- `SMTP_PORT`: SMTP server port (commonly `587`)
- `SMTP_USER`: SMTP username/login
- `SMTP_PASSWORD`: SMTP password or app password
- `TO_EMAIL`: your email address (recipient)
- `FROM_EMAIL` (optional): sender email (defaults to `SMTP_USER`)
- `NEWS_COUNTRY` (optional): country code for headlines, default `us`
- `NEWS_CATEGORY` (optional): business, sports, technology, etc.
- `STATE_FILE` (optional): file that stores already-sent article URLs, default `.news_seen.json`
- `MAX_ITEMS_PER_EMAIL` (optional): max headlines in one alert, default `10`

### 2) Run it once manually

```bash
NEWS_API_KEY=... \
SMTP_HOST=... \
SMTP_PORT=587 \
SMTP_USER=... \
SMTP_PASSWORD=... \
TO_EMAIL=you@example.com \
FROM_EMAIL=you@example.com \
python3 news_email_task.py
```

### 3) Run it automatically (cron example: every 15 minutes)

```cron
*/15 * * * * cd /workspace/cautious-system && NEWS_API_KEY=... SMTP_HOST=... SMTP_PORT=587 SMTP_USER=... SMTP_PASSWORD=... TO_EMAIL=you@example.com FROM_EMAIL=you@example.com /usr/bin/python3 news_email_task.py >> news_email_task.log 2>&1
```

The script only emails you for newly-seen article URLs.
