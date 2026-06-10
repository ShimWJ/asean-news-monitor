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


def clean_text(text):
    """RSS 요약문에 들어 있는 HTML 태그를 간단히 제거합니다."""
    if not text:
        return ""

    text = re.sub(r"<[^>]+>", "", text)
    text = unescape(text)
    return text.strip()


@st.cache_data(ttl=1800)
def load_rss():
    """RSS 피드에서 기사 목록을 가져옵니다."""
    feed = feedparser.parse(RSS_URL)

    articles = []

    for entry in feed.entries[:10]:
        article = {
            "title": entry.get("title", "제목 없음"),
            "source": feed.feed.get("title", "RSS Feed"),
            "published": entry.get("published", "날짜 정보 없음"),
            "summary": clean_text(entry.get("summary", "")),
            "url": entry.get("link", "")
        }

        articles.append(article)

    return articles


st.title("ASEAN / Southeast Asia News Monitor")

st.write(
    "동남아시아·ASEAN 관련 뉴스를 모니터링하고, 주요 이슈를 정리하는 페이지입니다."
)

st.divider()

st.subheader("RSS 테스트")

st.caption("오늘은 실제 RSS 피드에서 최신 기사 목록을 가져오는 단계입니다.")

articles = load_rss()

if len(articles) == 0:
    st.error("RSS에서 기사를 가져오지 못했습니다.")
else:
    st.success(f"RSS에서 기사 {len(articles)}개를 가져왔습니다.")

    for article in articles:
        with st.container():
            st.markdown(f"### {article['title']}")
            st.write(f"**출처:** {article['source']}")
            st.write(f"**발행일:** {article['published']}")

            if article["summary"]:
                st.write(article["summary"])

            if article["url"]:
                st.link_button("원문 보기", article["url"])

            st.divider()
