import re
from html import unescape

import streamlit as st
import feedparser


st.set_page_config(
    page_title="ASEAN News Monitor",
    page_icon="🌏",
    layout="wide"
)


FEEDS = [
    {
        "name": "ASEAN Official News",
        "url": "https://asean.org/category/news/feed/",
    },
    {
        "name": "CNA Asia",
        "url": "https://www.channelnewsasia.com/api/v1/rss-outbound-feed?_format=xml&category=6511",
    },
    {
        "name": "Fulcrum by ISEAS",
        "url": "https://fulcrum.sg/feed/",
    },
]


KEYWORDS = [
    "ASEAN",
    "Southeast Asia",
    "South-East Asia",
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
    "RCEP",
    "SEA"
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
def load_rss_from_multiple_sources():
    """여러 RSS 피드에서 기사를 가져오고, 관련 기사만 골라냅니다."""
    all_articles = []
    filtered_articles = []

    seen_urls = set()

    for feed_info in FEEDS:
        feed_name = feed_info["name"]
        feed_url = feed_info["url"]

        feed = feedparser.parse(feed_url)

        for entry in feed.entries[:20]:
            title = entry.get("title", "제목 없음")
            summary = clean_text(entry.get("summary", ""))
            url = entry.get("link", "")
            published = entry.get("published", "날짜 정보 없음")

            if not url:
                continue

            if url in seen_urls:
                continue

            seen_urls.add(url)

            matched_keywords = find_matched_keywords(title, summary)

            article = {
                "title": title,
                "source": feed_name,
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
    "동남아시아·ASEAN 관련 공개 뉴스와 분석 글을 모니터링하는 페이지입니다."
)

st.divider()

st.subheader("ASEAN / 동남아 관련 뉴스")

st.caption(
    "The Diplomat은 구독 제한이 있어 제외했고, 우선 공개 전문을 볼 수 있는 출처 위주로 RSS를 연결했습니다."
)

all_articles, filtered_articles = load_rss_from_multiple_sources()

st.write(f"전체 RSS 기사 수: **{len(all_articles)}개**")
st.write(f"동남아·ASEAN 관련 기사 수: **{len(filtered_articles)}개**")

with st.expander("현재 사용 중인 RSS 출처 보기"):
    for feed in FEEDS:
        st.write(f"- {feed['name']}")

with st.expander("현재 사용 중인 필터 키워드 보기"):
    st.write(", ".join(KEYWORDS))

st.divider()

if len(filtered_articles) == 0:
    st.warning("현재 RSS 기사 중에서 동남아·ASEAN 관련 키워드가 들어간 기사를 찾지 못했습니다.")
    st.info("RSS 연결 실패가 아니라, 이번에 가져온 기사 중 조건에 맞는 기사가 없을 수 있습니다.")
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
