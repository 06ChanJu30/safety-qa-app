import streamlit as st
import pandas as pd
import json
import os

# 1. 페이지 기본 설정
st.set_page_config(page_title="안전보건 질의회시 검색기", page_icon="💡", layout="centered")

st.title("💡 안전보건 질의회시 통합 검색")
st.caption("폭염 관련 산업안전보건규칙 및 산업안전보건법 질의회시 검색 엔진")

# 2. 데이터 불러오기 (app.py와 qa_database.json이 같은 폴더에 있음)
current_dir = os.path.dirname(os.path.abspath(__file__))
JSON_FILE_PATH = os.path.join(current_dir, "qa_database.json")

@st.cache_data
def load_qa_data():
    if not os.path.exists(JSON_FILE_PATH):
        return pd.DataFrame()
    with open(JSON_FILE_PATH, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return pd.DataFrame(data)

df = load_qa_data()

if df.empty:
    st.warning("데이터베이스 파일(qa_database.json)이 비어있거나 찾을 수 없습니다.")
    st.write(f"경로 확인: {JSON_FILE_PATH}") # 경로가 어디를 가리키는지 화면에 표시
    st.stop()

# 3. 검색 필터 (문서 종류 선택)
doc_types = ["전체"] + list(df['doc_type'].unique())
selected_doc = st.radio("📑 검색 대상 문서", doc_types, horizontal=True)

# 4. 검색창
query = st.text_input("🔍 검색어를 입력하세요 (예: 폭염, 휴식, 119, 그늘막)")

if query:
    # 선택한 문서 종류에 따라 데이터 필터링
    if selected_doc != "전체":
        filtered_df = df[df['doc_type'] == selected_doc]
    else:
        filtered_df = df
        
    # 질문이나 답변에 검색어가 포함된 결과 찾기
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
        # 5. 아코디언(Expander) 형태로 결과 출력
        for i, row in result_df.iterrows():
            expander_label = f"[{row['doc_type']}] {row['question']}"
            with st.expander(expander_label):
                st.markdown(f"**📌 분류:** {row['category']}")
                st.markdown(f"**📝 질문:** {row['question']}")
                st.info(f"**💡 답변:**\n\n{row['answer']}")
                st.caption(f"행정해석 근거: {row['reference']}")
