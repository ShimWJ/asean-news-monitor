import os

import pandas as pd
import streamlit as st

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


st.set_page_config(
    page_title="ASEAN News Monitor",
    page_icon="🌏",
    layout="wide"
)


@st.cache_data(ttl=300)
def load_saved_articles():
    """저장된 기사 CSV를 읽습니다."""
    if not os.path.exists(CSV_FILE):
        return pd.DataFrame(columns=COLUMNS)

    try:
        df = pd.read_csv(CSV_FILE)
    except pd.errors.EmptyDataError:
        return pd.DataFrame(columns=COLUMNS)

    for column in COLUMNS:
        if column not in df.columns:
            df[column] = ""

    df = df[COLUMNS]
    df = df.fillna("")

    df["published_datetime"] = pd.to_datetime(
        df["published_iso"],
        errors="coerce",
        utc=True,
    )

    df = df.sort_values(
        by="published_datetime",
        ascending=False,
        na_position="last",
    )

    return df


def filter_by_period(df, selected_period):
    """선택한 기간에 맞는 기사만 남깁니다."""
    if selected_period == "전체 보기":
        return df

    now = pd.Timestamp.now(tz="UTC")

    if selected_period == "최근 7일":
        cutoff_date = now - pd.Timedelta(days=7)
    elif selected_period == "최근 30일":
        cutoff_date = now - pd.Timedelta(days=30)
    else:
        return df

    return df[
        df["published_datetime"].notna()
        & (df["published_datetime"] >= cutoff_date)
    ]


def filter_by_topic(df, selected_topic):
    """선택한 주제에 맞는 기사만 남깁니다."""
    if selected_topic == "전체 주제":
        return df

    def has_topic(topics_text):
        topics = [topic.strip() for topic in str(topics_text).split(",")]
        return selected_topic in topics

    return df[df["topics"].apply(has_topic)]


def filter_by_search_keyword(df, search_keyword):
    """검색어가 들어간 기사만 남깁니다."""
    search_keyword = search_keyword.strip().lower()

    if search_keyword == "":
        return df

    search_area = (
        df["title"].astype(str)
        + " "
        + df["summary"].astype(str)
        + " "
        + df["source"].astype(str)
        + " "
        + df["matched_keywords"].astype(str)
        + " "
        + df["topics"].astype(str)
    ).str.lower()

    return df[search_area.str.contains(search_keyword, regex=False, na=False)]


def count_topics(df):
    """현재 기사 목록에서 주제별 기사 수를 셉니다."""
    topic_counts = {}

    for topics_text in df["topics"]:
        topics = [topic.strip() for topic in str(topics_text).split(",")]

        for topic in topics:
            if topic == "":
                continue

            if topic not in topic_counts:
                topic_counts[topic] = 0

            topic_counts[topic] += 1

    return topic_counts


st.title("ASEAN / Southeast Asia News Monitor")

st.write(
    "동남아시아·ASEAN 관련 공개 뉴스와 분석 글을 모니터링하는 페이지입니다."
)

st.divider()

st.subheader("저장된 ASEAN / 동남아 관련 뉴스")

st.caption(
    "이제 앱은 RSS를 실시간으로 직접 읽는 대신, 수집 스크립트가 저장한 CSV 파일을 읽습니다."
)

df = load_saved_articles()

if len(df) == 0:
    st.warning("아직 저장된 기사가 없습니다.")
    st.info(
        "GitHub Actions에서 뉴스 수집 작업을 한 번 실행하면 "
        "`saved_articles.csv` 파일이 생기고, 여기에 기사가 저장됩니다."
    )
    st.stop()

st.write(f"저장된 기사 수: **{len(df)}개**")

if "collected_at" in df.columns and len(df["collected_at"]) > 0:
    last_collected_at = df["collected_at"].max()
    st.write(f"마지막 수집 시각: **{last_collected_at} UTC**")

st.divider()

source_names = ["전체 보기"]

for source in sorted(df["source"].unique()):
    if source:
        source_names.append(source)

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

articles_to_show = df.copy()

if selected_source != "전체 보기":
    articles_to_show = articles_to_show[
        articles_to_show["source"] == selected_source
    ]

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

with st.expander("현재 사용 중인 관련 기사 필터 키워드 보기"):
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
    for _, article in articles_to_show.iterrows():
        with st.container():
            st.markdown(f"### {article['title']}")
            st.write(f"**출처:** {article['source']}")
            st.write(f"**발행일:** {article['published_date']}")

            if article["topics"]:
                st.write(f"**주제:** {article['topics']}")

            if article["matched_keywords"]:
                st.write(f"**감지된 키워드:** {article['matched_keywords']}")

            if article["summary"]:
                st.write(article["summary"])

            if article["url"]:
                st.link_button("원문 보기", article["url"])

            st.divider()
