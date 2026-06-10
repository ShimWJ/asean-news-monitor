import re
from html import unescape
from datetime import datetime, timedelta, timezone

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
]


TOPICS = {
    "정치/외교": [
        "ASEAN summit",
        "foreign minister",
        "diplomacy",
        "dialogue",
        "statement",
        "secretary-general",
        "cooperation",
        "partnership",
    ],
    "안보": [
        "security",
        "defence",
        "defense",
        "military",
        "maritime",
        "South China Sea",
        "coast guard",
        "navy",
        "conflict",
    ],
    "경제/무역": [
        "economy",
        "economic",
        "trade",
        "investment",
        "supply chain",
        "RCEP",
        "digital economy",
        "market",
        "growth",
        "tariff",
    ],
    "미얀마": [
        "Myanmar",
        "junta",
        "NUG",
        "NLD",
        "Rohingya",
        "military regime",
    ],
    "기후/환경": [
        "climate",
        "environment",
        "energy",
        "renewable",
        "green",
        "flood",
        "haze",
        "disaster",
    ],
    "보건/사회": [
        "health",
        "education",
        "labour",
        "labor",
        "migration",
        "tourism",
        "youth",
        "women",
    ],
}


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
            published_text = entry.get("published", "날짜 정보 없음")
            published_datetime = parse_published_datetime(entry)

            if not url:
                continue

            if url in seen_urls:
                continue

            seen_urls.add(url)

            matched_keywords = find_matched_keywords(title, summary)
            topics = find_topics(title, summary)

            article = {
                "title": title,
                "source": feed_name,
                "published_text": published_text,
                "published_datetime": published_datetime,
                "display_date": format_date(published_datetime, published_text),
                "summary": summary,
                "url": url,
                "matched_keywords": matched_keywords,
                "topics": topics,
            }

            all_articles.append(article)

            if len(matched_keywords) > 0:
                filtered_articles.append(article)

    old_date = datetime(1970, 1, 1, tzinfo=timezone.utc)

    all_articles.sort(
        key=lambda article: article["published_datetime"] or old_date,
        reverse=True,
    )

    filtered_articles.sort(
        key=lambda article: article["published_datetime"] or old_date,
        reverse=True,
    )

    return all_articles, filtered_articles


def filter_by_source(articles, selected_source):
    """선택한 출처에 맞는 기사만 남깁니다."""
    if selected_source == "전체 보기":
        return articles

    result = []

    for article in articles:
        if article["source"] == selected_source:
            result.append(article)

    return result


def filter_by_search_keyword(articles, search_keyword):
    """검색어가 들어간 기사만 남깁니다."""
    search_keyword = search_keyword.strip().lower()

    if search_keyword == "":
        return articles

    result = []

    for article in articles:
        search_area = " ".join(
            [
                article["title"],
                article["summary"],
                article["source"],
                " ".join(article["matched_keywords"]),
                " ".join(article["topics"]),
            ]
        ).lower()

        if search_keyword in search_area:
            result.append(article)

    return result


def filter_by_period(articles, selected_period):
    """선택한 기간에 맞는 기사만 남깁니다."""
    if selected_period == "전체 보기":
        return articles

    now = datetime.now(timezone.utc)

    if selected_period == "최근 7일":
        cutoff_date = now - timedelta(days=7)
    elif selected_period == "최근 30일":
        cutoff_date = now - timedelta(days=30)
    else:
        return articles

    result = []

    for article in articles:
        if article["published_datetime"] is None:
            continue

        if article["published_datetime"] >= cutoff_date:
            result.append(article)

    return result


def filter_by_topic(articles, selected_topic):
    """선택한 주제에 맞는 기사만 남깁니다."""
    if selected_topic == "전체 주제":
        return articles

    result = []

    for article in articles:
        if selected_topic in article["topics"]:
            result.append(article)

    return result


def count_topics(articles):
    """현재 기사 목록에서 주제별 기사 수를 셉니다."""
    topic_counts = {}

    for article in articles:
        for topic in article["topics"]:
            if topic not in topic_counts:
                topic_counts[topic] = 0

            topic_counts[topic] += 1

    return topic_counts


st.title("ASEAN / Southeast Asia News Monitor")

st.write(
    "동남아시아·ASEAN 관련 공개 뉴스와 분석 글을 모니터링하는 페이지입니다."
)

st.divider()

st.subheader("ASEAN / 동남아 관련 뉴스")

st.caption(
    "공개적으로 원문을 볼 수 있는 출처 위주로 RSS를 연결했습니다."
)

all_articles, filtered_articles = load_rss_from_multiple_sources()

st.write(f"전체 RSS 기사 수: **{len(all_articles)}개**")
st.write(f"동남아·ASEAN 관련 기사 수: **{len(filtered_articles)}개**")

st.divider()

source_names = ["전체 보기"]

for feed in FEEDS:
    source_names.append(feed["name"])

period_options = [
    "전체 보기",
    "최근 7일",
    "최근 30일",
]

topic_options = ["전체 주제"]

for topic_name in TOPICS.keys():
    topic_options.append(topic_name)

topic_options.append("기타")


col1, col2, col3 = st.columns(3)

with col1:
    selected_source = st.selectbox(
        "출처 선택",
        source_names,
    )

with col2:
    selected_period = st.selectbox(
        "기간 선택",
        period_options,
    )

with col3:
    selected_topic = st.selectbox(
        "주제 선택",
        topic_options,
    )

search_keyword = st.text_input(
    "검색어",
    placeholder="예: Myanmar, Vietnam, South China Sea, trade",
)

articles_to_show = filtered_articles

articles_to_show = filter_by_source(articles_to_show, selected_source)
articles_to_show = filter_by_period(articles_to_show, selected_period)
articles_to_show = filter_by_topic(articles_to_show, selected_topic)
articles_to_show = filter_by_search_keyword(articles_to_show, search_keyword)

st.write(f"화면에 표시되는 기사 수: **{len(articles_to_show)}개**")

st.caption(
    "참고: 관련 기사 필터 키워드는 '동남아·ASEAN 관련 기사인지' 판단하는 기준이고, "
    "주제 키워드는 그 기사를 정치/외교, 안보, 경제/무역 등으로 나누는 기준입니다."
)

with st.expander("주제 분류 기준 보기"):
    if selected_topic == "전체 주제":
        st.write("각 주제는 아래 키워드 중 하나가 기사 제목이나 요약문에 포함될 때 자동으로 붙습니다.")

        for topic_name, topic_keywords in TOPICS.items():
            st.markdown(f"**{topic_name}**")
            st.write(", ".join(topic_keywords))

        st.markdown("**기타**")
        st.write("위 주제 키워드가 하나도 감지되지 않은 기사입니다.")

    elif selected_topic == "기타":
        st.write("기타는 아래 주제 키워드가 하나도 감지되지 않은 기사입니다.")

        for topic_name, topic_keywords in TOPICS.items():
            st.markdown(f"**{topic_name}**")
            st.write(", ".join(topic_keywords))

    else:
        st.write(f"현재 선택한 주제는 **{selected_topic}**입니다.")
        st.write("이 주제는 아래 키워드 중 하나가 기사 제목이나 요약문에 포함될 때 붙습니다.")
        st.info(", ".join(TOPICS[selected_topic]))

with st.expander("현재 사용 중인 RSS 출처 보기"):
    for feed in FEEDS:
        st.write(f"- {feed['name']}")

with st.expander("현재 사용 중인 필터 키워드 보기"):
    st.write(", ".join(KEYWORDS))

with st.expander("현재 기사 목록의 주제별 기사 수 보기"):
    topic_counts = count_topics(articles_to_show)

    if len(topic_counts) == 0:
        st.write("현재 조건에 맞는 기사가 없습니다.")
    else:
        for topic_name, count in topic_counts.items():
            st.write(f"- {topic_name}: {count}개")

st.divider()

if len(articles_to_show) == 0:
    st.warning("현재 선택한 조건에 맞는 기사가 없습니다.")
    st.info("검색어를 지우거나, 기간/출처/주제 조건을 넓혀보세요.")
else:
    for article in articles_to_show:
        with st.container():
            st.markdown(f"### {article['title']}")
            st.write(f"**출처:** {article['source']}")
            st.write(f"**발행일:** {article['display_date']}")

            if article["topics"]:
                st.write(f"**주제:** {', '.join(article['topics'])}")

            if article["matched_keywords"]:
                st.write(f"**감지된 키워드:** {', '.join(article['matched_keywords'])}")

            if article["summary"]:
                st.write(article["summary"])

            if article["url"]:
                st.link_button("원문 보기", article["url"])

            st.divider()
