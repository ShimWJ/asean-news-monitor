import csv
import os
import re
from datetime import datetime, timezone
from html import unescape

import feedparser

from config import FEEDS, KEYWORDS, TOPICS


CSV_FILE = "saved_articles.csv"

COLUMNS = [
    "title",
    "source",
    "published_date",
    "published_raw",
    "published_iso",
    "summary",
    "url",
    "matched_keywords",
    "topics",
    "collected_at",
]


def clean_text(text):
    """RSS 요약문에 들어 있는 HTML 태그를 간단히 제거합니다."""
    if not text:
        return ""

    text = re.sub(r"<[^>]+>", "", text)
    text = unescape(text)
    text = " ".join(text.split())
    return text.strip()


def find_matched_keywords(title, summary, source):
    """제목, 요약문, 출처명에서 동남아·ASEAN 관련 키워드를 찾습니다."""
    text = f"{title} {summary} {source}".lower()

    matched = []

    for keyword in KEYWORDS:
        if keyword.lower() in text:
            matched.append(keyword)

    return matched


def find_topics(title, summary):
    """제목과 요약문을 보고 기사 주제를 분류합니다."""
    text = f"{title} {summary}".lower()

    matched_topics = []

    for topic_name, topic_keywords in TOPICS.items():
        for keyword in topic_keywords:
            if keyword.lower() in text:
                matched_topics.append(topic_name)
                break

    if len(matched_topics) == 0:
        matched_topics.append("기타")

    return matched_topics


def parse_published_datetime(entry):
    """RSS 발행일을 파이썬 날짜 형식으로 바꿉니다."""
    published_parsed = entry.get("published_parsed")

    if published_parsed is None:
        published_parsed = entry.get("updated_parsed")

    if published_parsed is None:
        return None

    try:
        return datetime(
            published_parsed.tm_year,
            published_parsed.tm_mon,
            published_parsed.tm_mday,
            published_parsed.tm_hour,
            published_parsed.tm_min,
            published_parsed.tm_sec,
            tzinfo=timezone.utc,
        )
    except Exception:
        return None


def format_date(dt, fallback_text):
    """화면에 보여줄 날짜 형식으로 바꿉니다."""
    if dt is None:
        return fallback_text or "날짜 정보 없음"

    return dt.strftime("%Y-%m-%d")


def read_existing_rows():
    """이미 저장된 CSV를 읽고, 기존 기사 URL 목록을 만듭니다."""
    if not os.path.exists(CSV_FILE):
        return [], set()

    rows = []
    seen_urls = set()

    with open(CSV_FILE, "r", encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)

        for row in reader:
            url = row.get("url", "")

            if not url:
                continue

            complete_row = {}

            for column in COLUMNS:
                complete_row[column] = row.get(column, "")

            rows.append(complete_row)
            seen_urls.add(url)

    return rows, seen_urls


def write_rows(rows):
    """전체 기사 목록을 CSV에 저장합니다."""
    rows = sorted(
        rows,
        key=lambda row: row.get("published_iso", ""),
        reverse=True,
    )

    with open(CSV_FILE, "w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=COLUMNS)
        writer.writeheader()
        writer.writerows(rows)


def collect_new_rows(seen_urls):
    """RSS에서 새 기사를 수집합니다."""
    new_rows = []
    collected_at = datetime.now(timezone.utc).isoformat()

    for feed_info in FEEDS:
        feed_name = feed_info["name"]
        feed_url = feed_info["url"]

        print(f"Collecting from: {feed_name}")

        feed = feedparser.parse(feed_url)

        for entry in feed.entries[:30]:
            title = entry.get("title", "제목 없음")
            summary = clean_text(entry.get("summary", ""))
            url = entry.get("link", "")
            published_raw = entry.get("published", "날짜 정보 없음")
            published_datetime = parse_published_datetime(entry)

            if not url:
                continue

            if url in seen_urls:
                continue

            matched_keywords = find_matched_keywords(title, summary, feed_name)

            if len(matched_keywords) == 0:
                continue

            topics = find_topics(title, summary)

            row = {
                "title": title,
                "source": feed_name,
                "published_date": format_date(published_datetime, published_raw),
                "published_raw": published_raw,
                "published_iso": published_datetime.isoformat() if published_datetime else "",
                "summary": summary[:800],
                "url": url,
                "matched_keywords": ", ".join(matched_keywords),
                "topics": ", ".join(topics),
                "collected_at": collected_at,
            }

            new_rows.append(row)
            seen_urls.add(url)

    return new_rows


def main():
    existing_rows, seen_urls = read_existing_rows()
    new_rows = collect_new_rows(seen_urls)

    all_rows = existing_rows + new_rows

    write_rows(all_rows)

    print(f"Existing rows: {len(existing_rows)}")
    print(f"New rows: {len(new_rows)}")
    print(f"Total rows: {len(all_rows)}")


if __name__ == "__main__":
    main()
