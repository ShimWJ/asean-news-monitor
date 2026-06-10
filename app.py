import hmac
import json
import os
import urllib.error
import urllib.request

import pandas as pd
import streamlit as st

from config import FEEDS, KEYWORDS


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


APP_TOPICS = {
    "정치/외교": [
        "ASEAN summit",
        "foreign minister",
        "diplomacy",
        "dialogue",
        "statement",
        "secretary-general",
        "cooperation",
        "partnership",
        "election",
        "democracy",
        "sanctions",
        "junta",
        "NUG",
        "NLD",
        "military regime",
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
        "civil war",
        "armed conflict",
        "rebel",
        "insurgent",
        "resistance forces",
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
        "humanitarian",
        "refugee",
        "Rohingya",
        "human rights",
    ],
}


st.set_page_config(
    page_title="ASEAN News Monitor",
    page_icon="🌏",
    layout="wide",
)


def get_secret(name, default=""):
    """Streamlit Secrets에서 값을 안전하게 가져옵니다."""
    try:
        return st.secrets.get(name, default)
    except Exception:
        return default


def classify_topics(title, summary):
    """기사 제목과 요약문을 기준으로 앱 화면용 주제를 다시 분류합니다."""
    text = f"{title} {summary}".lower()

    matched_topics = []

    for topic_name, topic_keywords in APP_TOPICS.items():
        for keyword in topic_keywords:
            if keyword.lower() in text:
                matched_topics.append(topic_name)
                break

    if len(matched_topics) == 0:
        matched_topics.append("기타")

    return matched_topics


def trigger_github_workflow():
    """GitHub Actions의 collect_news.yml workflow를 실행합니다."""
    github_token = str(get_secret("GITHUB_TOKEN", "")).strip()
    github_repo = str(get_secret("GITHUB_REPO", "")).strip()
    github_branch = str(get_secret("GITHUB_BRANCH", "main")).strip()
    workflow_file = str(get_secret("GITHUB_WORKFLOW_FILE", "collect_news.yml")).strip()

    missing_items = []

    if not github_token:
        missing_items.append("GITHUB_TOKEN")

    if not github_repo:
        missing_items.append("GITHUB_REPO")

    if len(missing_items) > 0:
        return False, f"Streamlit Secrets에 {', '.join(missing_items)} 값이 없습니다."

    if "여기에" in github_token or "토큰" in github_token:
        return False, "GITHUB_TOKEN에 예시 문구가 들어가 있습니다. 실제 GitHub 토큰으로 바꿔주세요."

    if "본인" in github_repo or "깃허브" in github_repo:
        return False, "GITHUB_REPO에 예시 문구가 들어가 있습니다. 예: your-id/asean-news-monitor 형식으로 바꿔주세요."

    try:
        github_token.encode("ascii")
        github_repo.encode("ascii")
        github_branch.encode("ascii")
        workflow_file.encode("ascii")
    except UnicodeEncodeError:
        return False, (
            "GitHub 설정값에 한글이나 특수 문자가 들어가 있습니다. "
            "GITHUB_TOKEN, GITHUB_REPO, GITHUB_BRANCH, GITHUB_WORKFLOW_FILE 값을 확인해 주세요."
        )

    if "/" not in github_repo:
        return False, "GITHUB_REPO는 your-github-id/asean-news-monitor 형식이어야 합니다."

    if github_repo.startswith("http"):
        return False, "GITHUB_REPO에는 GitHub 주소 전체가 아니라 your-github-id/asean-news-monitor 형식만 넣어주세요."

    api_url = (
        f"https://api.github.com/repos/"
        f"{github_repo}/actions/workflows/{workflow_file}/dispatches"
    )

    payload = {
        "ref": github_branch,
    }

    request = urllib.request.Request(
        api_url,
        data=json.dumps(payload).encode("utf-8"),
        method="POST",
        headers={
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {github_token}",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "asean-news-monitor-streamlit-app",
        },
    )

    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            status_code = response.status

        if 200 <= status_code < 300:
            return True, "뉴스 수집 작업을 GitHub Actions에 요청했습니다."

        return False, f"GitHub API 응답이 예상과 다릅니다. 상태 코드: {status_code}"

    except urllib.error.HTTPError as error:
        error_body = error.read().decode("utf-8", errors="replace")
        return False, f"GitHub API 오류 {error.code}: {error_body}"

    except Exception as error:
        return False, f"요청 중 오류가 발생했습니다: {error}"


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

    df["app_topics"] = df.apply(
        lambda row: ", ".join(
            classify_topics(
                row["title"],
                row["summary"],
            )
        ),
        axis=1,
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

    return df[df["app_topics"].apply(has_topic)]


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
        + df["app_topics"].astype(str)
    ).str.lower()

    return df[search_area.str.contains(search_keyword, regex=False, na=False)]


def count_topics(df):
    """현재 기사 목록에서 주제별 기사 수를 셉니다."""
    topic_counts = {}

    for topics_text in df["app_topics"]:
        topics = [topic.strip() for topic in str(topics_text).split(",")]

        for topic in topics:
            if topic == "":
                continue

            if topic not in topic_counts:
                topic_counts[topic] = 0

            topic_counts[topic] += 1

    return topic_counts


if "admin_authenticated" not in st.session_state:
    st.session_state.admin_authenticated = False


st.title("ASEAN / Southeast Asia News Monitor")

st.write(
    "동남아시아·ASEAN 관련 공개 뉴스와 분석 글을 모니터링하는 페이지입니다."
)

st.divider()

with st.expander("관리자 기능: 뉴스 수집 실행"):
    st.write(
        "관리자 비밀번호를 입력하면 GitHub Actions의 뉴스 수집 작업을 앱에서 실행할 수 있습니다."
    )

    admin_password = get_secret("ADMIN_PASSWORD")

    if not admin_password:
        st.warning("Streamlit Secrets에 ADMIN_PASSWORD가 설정되어 있지 않습니다.")
    else:
        password_input = st.text_input(
            "관리자 비밀번호",
            type="password",
            placeholder="관리자 비밀번호 입력",
        )

        if st.button("관리자 확인"):
            if hmac.compare_digest(password_input, admin_password):
                st.session_state.admin_authenticated = True
                st.success("관리자 확인이 완료되었습니다.")
            else:
                st.session_state.admin_authenticated = False
                st.error("비밀번호가 맞지 않습니다.")

        if st.session_state.admin_authenticated:
            st.success("현재 관리자 모드입니다.")

            if st.button("뉴스 수집 실행"):
                with st.spinner("GitHub Actions에 뉴스 수집 작업을 요청하는 중입니다..."):
                    success, message = trigger_github_workflow()

                if success:
                    st.success(message)
                    st.info(
                        "수집 작업은 GitHub Actions에서 백그라운드로 실행됩니다. "
                        "보통 1~3분 뒤 saved_articles.csv가 업데이트됩니다. "
                        "잠시 후 앱을 새로고침해 주세요."
                    )
                else:
                    st.error(message)

            github_repo = get_secret("GITHUB_REPO")
            workflow_file = get_secret("GITHUB_WORKFLOW_FILE", "collect_news.yml")

            if github_repo:
                actions_url = (
                    f"https://github.com/{github_repo}/actions/workflows/{workflow_file}"
                )
                st.link_button("GitHub Actions 실행 상태 보기", actions_url)

            if st.button("관리자 모드 해제"):
                st.session_state.admin_authenticated = False
                st.rerun()


st.divider()

st.subheader("저장된 ASEAN / 동남아 관련 뉴스")

st.caption(
    "이 앱은 수집 스크립트가 저장한 saved_articles.csv 파일을 읽어서 기사 목록을 보여줍니다."
)

df = load_saved_articles()

if len(df) == 0:
    st.warning("아직 저장된 기사가 없습니다.")
    st.info(
        "위의 관리자 기능에서 뉴스 수집을 실행하면 "
        "`saved_articles.csv` 파일이 생성되거나 업데이트됩니다."
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

for topic_name in APP_TOPICS.keys():
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
    "주제 키워드는 그 기사를 정치/외교, 안보, 경제/무역 등으로 나누는 기준입니다. "
    "미얀마는 국가명이므로 주제 선택에서는 제외했습니다."
)

with st.expander("주제 분류 기준 보기"):
    if selected_topic == "전체 주제":
        st.write("각 주제는 아래 키워드 중 하나가 기사 제목이나 요약문에 포함될 때 자동으로 붙습니다.")

        for topic_name, topic_keywords in APP_TOPICS.items():
            st.markdown(f"**{topic_name}**")
            st.write(", ".join(topic_keywords))

        st.markdown("**기타**")
        st.write("위 주제 키워드가 하나도 감지되지 않은 기사입니다.")

    elif selected_topic == "기타":
        st.write("기타는 아래 주제 키워드가 하나도 감지되지 않은 기사입니다.")

        for topic_name, topic_keywords in APP_TOPICS.items():
            st.markdown(f"**{topic_name}**")
            st.write(", ".join(topic_keywords))

    else:
        st.write(f"현재 선택한 주제는 **{selected_topic}**입니다.")
        st.write("이 주제는 아래 키워드 중 하나가 기사 제목이나 요약문에 포함될 때 붙습니다.")
        st.info(", ".join(APP_TOPICS[selected_topic]))

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

            if article["app_topics"]:
                st.write(f"**주제:** {article['app_topics']}")

            if article["matched_keywords"]:
                st.write(f"**감지된 키워드:** {article['matched_keywords']}")

            if article["summary"]:
                st.write(article["summary"])

            if article["url"]:
                st.link_button("원문 보기", article["url"])

            st.divider()
