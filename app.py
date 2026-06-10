import streamlit as st

st.set_page_config(
    page_title="ASEAN News Monitor",
    page_icon="🌏",
    layout="wide"
)

st.title("ASEAN / Southeast Asia News Monitor")

st.write(
    "동남아시아·ASEAN 관련 뉴스를 모니터링하고, 주요 이슈를 정리하는 페이지입니다."
)

st.divider()

st.subheader("이번 주 주요 뉴스")

news_list = [
    {
        "title": "ASEAN 디지털경제 협정 논의 확대",
        "category": "경제",
        "source": "Example News",
        "date": "2026-06-10",
        "summary": "ASEAN 회원국들이 디지털 무역, 전자상거래, 데이터 이동 규칙을 논의했습니다.",
        "url": "https://example.com/news-1"
    },
    {
        "title": "남중국해 관련 긴장 지속",
        "category": "안보",
        "source": "Example News",
        "date": "2026-06-09",
        "summary": "남중국해를 둘러싼 해양 안보 이슈가 이번 주에도 주요 관심사로 다뤄졌습니다.",
        "url": "https://example.com/news-2"
    },
    {
        "title": "미얀마 정세 관련 국제사회 논의",
        "category": "정치",
        "source": "Example News",
        "date": "2026-06-08",
        "summary": "미얀마 정세와 인도주의 지원 문제를 두고 ASEAN과 주변국의 논의가 이어졌습니다.",
        "url": "https://example.com/news-3"
    }
]

for news in news_list:
    with st.container():
        st.markdown(f"### [{news['category']}] {news['title']}")
        st.write(f"**출처:** {news['source']}")
        st.write(f"**날짜:** {news['date']}")
        st.write(news["summary"])
        st.link_button("기사 원문 보기", news["url"])
        st.divider()
