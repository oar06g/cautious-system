#!/usr/bin/env python3
"""Send email alerts for newly published news headlines.

Usage (example with cron):
*/15 * * * * NEWS_API_KEY=... SMTP_HOST=... SMTP_PORT=587 SMTP_USER=... SMTP_PASSWORD=... TO_EMAIL=you@example.com FROM_EMAIL=you@example.com python3 /path/to/news_email_task.py
"""

from __future__ import annotations

import json
import os
import smtplib
from datetime import datetime, timezone
from email.mime.text import MIMEText
from pathlib import Path
from typing import Any
from urllib.parse import urlencode
from urllib.request import Request, urlopen

STATE_FILE = Path(os.getenv("STATE_FILE", ".news_seen.json"))
NEWS_API_ENDPOINT = "https://newsapi.org/v2/top-headlines"
MAX_ITEMS_PER_EMAIL = int(os.getenv("MAX_ITEMS_PER_EMAIL", "10"))


def env(name: str, default: str | None = None) -> str:
    value = os.getenv(name, default)
    if value is None or value == "":
        raise ValueError(f"Missing required environment variable: {name}")
    return value


def load_seen() -> set[str]:
    if not STATE_FILE.exists():
        return set()

    with STATE_FILE.open("r", encoding="utf-8") as f:
        data = json.load(f)

    return set(data.get("seen_urls", []))


def save_seen(seen_urls: set[str]) -> None:
    payload = {
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "seen_urls": sorted(seen_urls),
    }
    with STATE_FILE.open("w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)


def fetch_headlines(api_key: str, country: str, category: str | None) -> list[dict[str, Any]]:
    params = {"country": country, "apiKey": api_key, "pageSize": MAX_ITEMS_PER_EMAIL}
    if category:
        params["category"] = category

    url = f"{NEWS_API_ENDPOINT}?{urlencode(params)}"
    req = Request(url, headers={"User-Agent": "news-email-task/1.0"})

    with urlopen(req, timeout=30) as response:
        body = response.read().decode("utf-8")

    data = json.loads(body)
    if data.get("status") != "ok":
        raise RuntimeError(f"News API request failed: {data}")

    return data.get("articles", [])


def format_email(new_articles: list[dict[str, Any]]) -> str:
    lines = ["New headlines detected:\n"]

    for i, article in enumerate(new_articles, start=1):
        title = article.get("title") or "(no title)"
        source = (article.get("source") or {}).get("name") or "Unknown source"
        url = article.get("url") or ""
        published_at = article.get("publishedAt") or ""
        lines.append(f"{i}. {title}")
        lines.append(f"   Source: {source}")
        if published_at:
            lines.append(f"   Published: {published_at}")
        if url:
            lines.append(f"   URL: {url}")
        lines.append("")

    return "\n".join(lines)


def send_email(subject: str, body: str) -> None:
    smtp_host = env("SMTP_HOST")
    smtp_port = int(env("SMTP_PORT", "587"))
    smtp_user = env("SMTP_USER")
    smtp_password = env("SMTP_PASSWORD")
    to_email = env("TO_EMAIL")
    from_email = env("FROM_EMAIL", smtp_user)

    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = from_email
    msg["To"] = to_email

    with smtplib.SMTP(smtp_host, smtp_port, timeout=30) as server:
        server.starttls()
        server.login(smtp_user, smtp_password)
        server.sendmail(from_email, [to_email], msg.as_string())


def main() -> None:
    api_key = env("NEWS_API_KEY")
    country = env("NEWS_COUNTRY", "us")
    category = os.getenv("NEWS_CATEGORY")

    seen_urls = load_seen()
    headlines = fetch_headlines(api_key=api_key, country=country, category=category)

    new_articles = []
    for article in headlines:
        article_url = article.get("url")
        if not article_url:
            continue
        if article_url in seen_urls:
            continue
        new_articles.append(article)

    if not new_articles:
        print("No new headlines found.")
        return

    subject = f"News alert: {len(new_articles)} new headline(s)"
    body = format_email(new_articles)
    send_email(subject, body)

    for article in new_articles:
        seen_urls.add(article["url"])

    save_seen(seen_urls)
    print(f"Sent alert for {len(new_articles)} new headlines.")


if __name__ == "__main__":
    main()
