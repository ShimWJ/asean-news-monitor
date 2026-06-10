import streamlit as st
import pandas as pd

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

df = pd.read_csv("news.csv")

for index, row in df.iterrows():
    with st.container():
        st.markdown(f"### [{row['category']}] {row['title']}")
        st.write(f"**출처:** {row['source']}")
        st.write(f"**날짜:** {row['date']}")
        st.write(row["summary"])
        st.link_button("기사 원문 보기", row["url"])
        st.divider()
