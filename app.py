import re
from html import unescape

import streamlit as st
import feedparser


st.set_page_config(
    page_title="ASEAN News Monitor",
    page_icon="🌏",
    layout="wide"
)


RSS_URL = "https://thediplomat.com/feed/"


KEYWORDS = [
    "ASEAN",
    "Southeast Asia",
    "SEA",
    "Myanmar",
    "Vietnam",
    "Thailand",
    "Indonesia",
    "Malaysia",
    "Philippines",
    "Singapore",
    "Cambodia",
    "Laos",
    "Brunei",
    "Timor-Leste",
    "East Timor",
    "South China Sea",
    "Mekong",
]


def clean_text(text):
    """RSS 요약문에 들어 있는 HTML 태그를 간단히 제거합니다."""
    if not text:
        return ""

    text = re.sub(r"<[^>]+>", "", text)
    text = unescape(text)
    return text.strip()


def find_matched_keywords(title, summary):
    """제목과 요약문에서 동남아·ASEAN 관련 키워드를 찾습니다."""
    text = f"{title} {summary}".lower()

    matched = []

    for keyword in KEYWORDS:
        if keyword.lower() in text:
            matched.append(keyword)

    return matched


@st.cache_data(ttl=1800)
def load_rss():
    """RSS 피드에서 기사 목록을 가져오고, 관련 기사만 골라냅니다."""
    feed = feedparser.parse(RSS_URL)

    all_articles = []
    filtered_articles = []

    for entry in feed.entries[:30]:
        title = entry.get("title", "제목 없음")
        summary = clean_text(entry.get("summary", ""))
        url = entry.get("link", "")
        published = entry.get("published", "날짜 정보 없음")
        source = feed.feed.get("title", "RSS Feed")

        matched_keywords = find_matched_keywords(title, summary)

        article = {
            "title": title,
            "source": source,
            "published": published,
            "summary": summary,
            "url": url,
            "matched_keywords": matched_keywords,
        }

        all_articles.append(article)

        if len(matched_keywords) > 0:
            filtered_articles.append(article)

    return all_articles, filtered_articles


st.title("ASEAN / Southeast Asia News Monitor")

st.write(
    "동남아시아·ASEAN 관련 뉴스를 모니터링하고, 주요 이슈를 정리하는 페이지입니다."
)

st.divider()

st.subheader("ASEAN / 동남아 관련 뉴스")

st.caption("RSS에서 가져온 기사 중, 관련 키워드가 포함된 기사만 보여줍니다.")

all_articles, filtered_articles = load_rss()

st.write(f"전체 RSS 기사 수: **{len(all_articles)}개**")
st.write(f"동남아·ASEAN 관련 기사 수: **{len(filtered_articles)}개**")

with st.expander("현재 사용 중인 필터 키워드 보기"):
    st.write(", ".join(KEYWORDS))

st.divider()

if len(filtered_articles) == 0:
    st.warning("현재 RSS 기사 중에서 동남아·ASEAN 관련 키워드가 들어간 기사를 찾지 못했습니다.")
    st.info("RSS 연결이 실패한 것은 아닙니다. 이번에 가져온 기사들 중 조건에 맞는 기사가 없다는 뜻입니다.")
else:
    for article in filtered_articles:
        with st.container():
            st.markdown(f"### {article['title']}")
            st.write(f"**출처:** {article['source']}")
            st.write(f"**발행일:** {article['published']}")

            if article["matched_keywords"]:
                st.write(f"**감지된 키워드:** {', '.join(article['matched_keywords'])}")

            if article["summary"]:
                st.write(article["summary"])

            if article["url"]:
                st.link_button("원문 보기", article["url"])

            st.divider()
