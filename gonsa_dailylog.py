import streamlit as st
import pandas as pd
from PIL import Image
from datetime import date

st.set_page_config(page_title="공사일보 자동화 프로그램", layout="wide")
st.title("📋 공사일보 자동화 프로그램 (v3.0)")

footer_html = """
<style>
.footer {
    position: fixed;
    left: 0;
    bottom: 0;
    width: 100%;
    background-color: #f1f1f1;
    color: #333;
    text-align: center;
    padding: 10px 0;
    font-size: 14px;
}
</style>
<div class="footer">
    © 2025 YourSiteName. Designed & Developed by YourName.
</div>
"""

# 푸터 렌더링
st.markdown(footer_html, unsafe_allow_html=True)

# 세션 상태 초기화 (최초 실행 시)
if "images" not in st.session_state:
    st.session_state.images = []
if "previews" not in st.session_state:
    st.session_state.previews = []
if "current" not in st.session_state:
    st.session_state.current = 0
if "data" not in st.session_state:
    st.session_state.data = []
if "completed" not in st.session_state:
    st.session_state.completed = False
if "default_date" not in st.session_state:
    st.session_state.default_date = date.today()
if "initialized" not in st.session_state:
    st.session_state.initialized = False

# 파일 업로드 (초기화 한 번만 진행)
st.markdown(
    '파일 첨부하기 (png, jpg, jpeg 등) ‼️PDF 업로드 불가‼️ *PDF->이미지변환 사이트주소 [https://www.ilovepdf.com/ko/pdf_to_jpg](https://www.ilovepdf.com/ko/pdf_to_jpg)*'
)
uploaded_files = st.file_uploader(
    "",  # st.markdown에 안내 문구를 넣었으므로, file_uploader의 라벨은 빈 문자열로 사용
    type=["png", "jpg", "jpeg"],
    accept_multiple_files=True
)


if uploaded_files and not st.session_state.initialized:
    st.session_state.initialized = True
    st.session_state.images = uploaded_files
    st.session_state.previews = [Image.open(f) for f in uploaded_files]
    # "장비" 필드를 추가하여 초기 데이터에 포함
    st.session_state.data = [{"날짜": "", "공종": "", "인원": 0, "장비": "", "내용": ""} for _ in uploaded_files]
    st.session_state.current = 0
    st.session_state.completed = False

# 업로드한 이미지 삭제 (삭제 후에는 루프 밖에서 처리)
if st.session_state.previews:
    st.markdown("### 🖼 업로드한 파일들")
    delete_idx = None
    thumbs = st.columns(len(st.session_state.previews))
    for i, col in enumerate(thumbs):
        with col:
            st.image(st.session_state.previews[i], caption=f"Page {i + 1}", width=100)
            if st.button("❌", key=f"delete_{i}"):
                delete_idx = i
    if delete_idx is not None:
        del st.session_state.images[delete_idx]
        del st.session_state.previews[delete_idx]
        del st.session_state.data[delete_idx]
        if st.session_state.current >= len(st.session_state.previews):
            st.session_state.current = max(0, len(st.session_state.previews) - 1)
        st.rerun()

# 현재 이미지에 대한 공사일보 입력폼 (아직 완료되지 않은 경우)
if st.session_state.previews and st.session_state.current < len(st.session_state.previews):
    idx = st.session_state.current
    total = len(st.session_state.previews)
    col1, col2 = st.columns([1, 2])

    with col1:
        st.image(st.session_state.previews[idx], caption=f"이미지 {idx + 1} / {total}", use_container_width=True)

    with col2:
        st.subheader("📝 공사일보 입력")
        saved_data = st.session_state.data[idx]
        with st.form(key=f"entry_form_{idx}"):
            날짜 = st.date_input("날짜", value=saved_data["날짜"] or st.session_state.default_date)
            공종 = st.text_input("공종명", value=saved_data["공종"])
            # 인원과 장비를 한 줄에 두 개의 컬럼으로 배치
            col_in, col_equ = st.columns(2)
            with col_in:
                인원 = st.number_input("인원", min_value=0, step=1, value=saved_data["인원"])
            with col_equ:
                장비 = st.text_input("장비", value=saved_data.get("장비", ""))
            내용 = st.text_area("공사일보 내용", value=saved_data["내용"], height=200)

            # 라디오 버튼: 기본 선택은 "저장 & 다음"
            action = st.radio("동작 선택", options=["이전", "저장 & 다음"], index=1)
            submitted = st.form_submit_button("확인")

            if submitted:
                st.session_state.data[idx] = {
                    "날짜": 날짜,
                    "공종": 공종,
                    "인원": 인원,
                    "장비": 장비,
                    "내용": 내용
                }
                if idx == 0:
                    st.session_state.default_date = 날짜

                if action == "이전":
                    st.session_state.current = max(0, idx - 1)
                else:  # "저장 & 다음"
                    if idx < total - 1:
                        st.session_state.current = idx + 1
                    else:
                        st.session_state.completed = True
                st.rerun()

# 아래 영역은 입력폼 제출할 때마다 즉시 업데이트됨
if st.session_state.previews:
    formatted_lines = []
    for entry in st.session_state.data:
        if entry["공종"] or entry["내용"]:
            # 장비 정보를 포함해서 표시 (예: "공종 (인원 / 장비: 장비입력)")
            line = f"{entry['공종']} ({entry['인원']} / 장비: {entry['장비']})\n{entry['내용']}"
            formatted_lines.append(line)
    total_personnel = sum(entry["인원"] for entry in st.session_state.data)
    # 각 항목의 장비 내용 중 빈 문자열은 제외하고, 쉼표로 나열
    equipment_entries = [entry["장비"] for entry in st.session_state.data if entry["장비"] != ""]
    equipment_line = ", ".join(equipment_entries)
    output_text = (
        f"날짜: {str(st.session_state.default_date)}\n\n"
        + "\n\n".join(formatted_lines)
        + f"\n\n총인원 : {total_personnel}"
        + f"\n\n장비: {equipment_line}"
    )
    st.markdown("### 📄 공사일보 취합 (수정가능)")
    st.text_area("복사 가능한 최종 텍스트", value=output_text, height=400)

    st.markdown("### 📊 전체 공사일보 결과")
    df = pd.DataFrame(st.session_state.data)
    st.dataframe(df)
