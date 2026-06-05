import streamlit as st
import pandas as pd
import json
import os

# 1. 페이지 기본 설정
st.set_page_config(page_title="안전보건 질의회시 검색기", page_icon="💡", layout="centered")

st.title("💡 안전보건 질의회시 통합 검색")
st.caption("폭염, 산안법, 중처법, 안전보건관리비 등 각종 안전보건 질의회시 통합 검색 엔진")

current_dir = os.path.dirname(os.path.abspath(__file__))

# 2. 모든 JSON 파일을 자동으로 찾아서 하나로 합치기 (만능 엔진 🌟)
@st.cache_data
def load_and_merge_data():
    all_data = []
    
    # 현재 폴더 안의 모든 파일을 확인해서 .json으로 끝나는 파일은 전부 읽어옵니다.
    for filename in os.listdir(current_dir):
        if filename.endswith(".json"):
            file_path = os.path.join(current_dir, filename)
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    all_data.extend(json.load(f))
            except Exception as e:
                st.warning(f"⚠️ {filename} 로드 중 오류 발생: {e}")
                
    df = pd.DataFrame(all_data)
    
    if not df.empty and 'doc_type' in df.columns:
        # 🌟 문서 이름 예쁘게 바꾸기 (중처법, 관리비 추가!)
        df['doc_type'] = df['doc_type'].replace({
            '산업안전보건법 질의회시집': '📘 산업안전보건법 질의회시',
            '폭염 산업안전보건규칙': '☀️ 폭염 및 온열질환 예방',
            '중대재해처벌법 질의회시': '⚖️ 중대재해처벌법 질의회시',
            '중대재해처벌법': '⚖️ 중대재해처벌법 질의회시', # 이름이 약간 다를 경우를 대비
            '안전보건관리비 질의회시': '💰 안전보건관리비 질의회시',
            '건설업 산업안전보건관리비': '💰 안전보건관리비 질의회시'
        })
        
    return df

df = load_and_merge_data()

# 에러 처리 (데이터를 하나도 못 불렀을 때)
if df.empty:
    st.error("데이터를 하나도 불러오지 못했습니다. 깃허브에 JSON 파일들이 잘 올라가 있는지 확인해주세요.")
    st.stop()

# 3. 검색 필터 생성
doc_types = ["전체"] + list(df['doc_type'].dropna().unique())
selected_doc = st.radio("📑 검색 대상 문서", doc_types, horizontal=True)

# 4. 검색창 (띄어쓰기 다중 키워드 지원)
query = st.text_input("🔍 검색어를 띄어쓰기로 여러 개 입력해보세요. (예: 도급인 안전관리자, 폭염 휴식)")

if query:
    if selected_doc != "전체":
        filtered_df = df[df['doc_type'] == selected_doc]
    else:
        filtered_df = df
        
    keywords = query.strip().split()
    
    # 교집합(AND) 검색 (입력한 단어가 모두 포함된 결과)
    mask = pd.Series([True] * len(filtered_df), index=filtered_df.index)
    for kw in keywords:
        kw_mask = filtered_df['question'].str.contains(kw, case=False, na=False) | \
                  filtered_df['answer'].str.contains(kw, case=False, na=False)
        mask = mask & kw_mask
