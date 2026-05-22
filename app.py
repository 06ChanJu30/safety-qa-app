import streamlit as st
import pandas as pd
import json
import os

# 1. 페이지 기본 설정
st.set_page_config(page_title="안전보건 질의회시 검색기", page_icon="💡", layout="centered")

st.title("💡 안전보건 질의회시 통합 검색")
st.caption("폭염 관련 산업안전보건규칙 및 산업안전보건법 질의회시 검색기")

# 2. 데이터 불러오기
# app.py와 qa_database.json이 같은 폴더에 있어야 합니다.
current_dir = os.path.dirname(os.path.abspath(__file__))
JSON_FILE_PATH = os.path.join(current_dir, "qa_database.json")

@st.cache_data
def load_qa_data():
    if not os.path.exists(JSON_FILE_PATH):
        return pd.DataFrame()
    try:
        with open(JSON_FILE_PATH, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return pd.DataFrame(data)
    except Exception as e:
        return pd.DataFrame()

df = load_qa_data()

# 데이터 로드 실패 시 에러 표시
if df.empty:
    st.error("데이터베이스 파일(qa_database.json)을 읽어올 수 없거나 파일이 비어있습니다. 깃허브에 파일이 정상적으로 업로드되었는지 확인해주세요.")
    st.stop()

# 3. 검색 필터 (문서 종류 선택)
# 데이터가 로드된 후 필터 생성
doc_types = ["전체"] + list(df['doc_type'].unique())
selected_doc = st.radio("📑 검색 대상 문서", doc_types, horizontal=True)

# 4. 검색창
query = st.text_input("🔍 검색어를 입력하세요 (예: 폭염, 도급, 안전보건관리책임자)")

# 5. 검색 결과 처리
if query:
    # 문서 종류 필터링
    if selected_doc != "전체":
        filtered_df = df[df['doc_type'] == selected_doc]
    else:
        filtered_df = df
        
    # 검색어 포함 여부 확인
    search_query = query.strip()
    result_df = filtered_df[
        filtered_df['question'].str.contains(search_query, case=False, na=False) | 
        filtered_df['answer'].str.contains(search_query, case=False, na=False)
    ]
    
    st.subheader(f"총 {len(result_df)}건의 검색 결과가 있습니다.")
    st.divider()
    
    if len(result_df) == 0:
        st.info("일치하는 질의회시 내용이 없습니다.")
    else:
        # 아코디언 형태로 결과 출력
        for i, row in result_df.iterrows():
            expander_label = f"[{row['doc_type']}] {row['question']}"
            with st.expander(expander_label):
                st.markdown(f"**📌 분류:** {row['category']}")
                st.markdown(f"**📝 질문:** {row['question']}")
                st.info(f"**💡 답변:**\n\n{row['answer']}")
                st.caption(f"행정해석 근거: {row['reference']}")

# 6. 하단 정보 및 문의처
st.divider()
st.markdown("### 📞 도움이 필요하신가요?")
st.write("검색 결과가 정확하지 않거나 시스템 오류가 발생 시 아래 연락처로 문의바랍니다.")

col1, col2 = st.columns([1, 2])
with col1:
    st.markdown("**이메일:** king990630@gmail.com")
    st.markdown("**카카오톡 ID:** lilaclil")

st.caption("📄 시스템 관련 문의사항은 언제든 환영합니다.")
