import streamlit as st

st.set_page_config(
    page_title="ASEAN News Monitor",
    page_icon="🌏",
    layout="wide"
)

st.title("ASEAN / Southeast Asia News Monitor")

st.write(
    "이 페이지는 앞으로 동남아시아·ASEAN 관련 뉴스를 모니터링하는 곳입니다."
)

st.divider()

st.subheader("현재 상태")

st.info("아직 뉴스 수집 기능은 없습니다. 먼저 Streamlit 앱 뼈대만 만든 상태입니다.")
