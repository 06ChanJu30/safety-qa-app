import streamlit as st
import pandas as pd
import json
import os

# 1. 페이지 기본 설정
st.set_page_config(page_title="안전보건 질의회시 검색기", page_icon="💡", layout="centered")

st.title("💡 안전보건 질의회시 통합 검색")
st.caption("폭염 관련 산업안전보건규칙 및 산업안전보건법 질의회시 검색 엔진")

# 2. 데이터 불러오기
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

if df.empty:
    st.error("데이터베이스 파일(qa_database.json)을 읽어올 수 없거나 파일이 비어있습니다.")
    st.stop()

# 3. 검색 필터 (문서 종류 선택)
doc_types = ["전체"] + list(df['doc_type'].unique())
selected_doc = st.radio("📑 검색 대상 문서", doc_types, horizontal=True)

# 4. 검색창
query = st.text_input("🔍 검색어를 띄어쓰기로 여러 개 입력해보세요. (예: 도급인 안전관리자, 폭염 휴식)")

# 5. 검색 및 연관 추천 로직
if query:
    # 5-1. 문서 종류 필터링
    if selected_doc != "전체":
        filtered_df = df[df['doc_type'] == selected_doc]
    else:
        filtered_df = df
        
    # 5-2. 띄어쓰기 기준 다중 키워드 추출
    keywords = query.strip().split()
    
    # 5-3. 교집합(AND) 검색: 입력한 단어가 모두 포함된 결과 찾기
    mask = pd.Series([True] * len(filtered_df), index=filtered_df.index)
    for kw in keywords:
        kw_mask = filtered_df['question'].str.contains(kw, case=False, na=False) | \
                  filtered_df['answer'].str.contains(kw, case=False, na=False)
        mask = mask & kw_mask
        
    result_df = filtered_df[mask]
    
    st.subheader(f"총 {len(result_df)}건의 검색 결과가 있습니다.")
    st.divider()
    
    # 5-4. 검색 결과가 없을 때 (유사 추천 기능 작동)
    if len(result_df) == 0:
        st.warning("정확히 일치하는 내용이 없습니다. 검색어를 줄이거나 다른 단어로 시도해 보세요.")
        
        # 합집합(OR) 검색: 단어 중 하나라도 포함된 결과 찾기
        or_mask = pd.Series([False] * len(filtered_df), index=filtered_df.index)
        for kw in keywords:
            kw_mask = filtered_df['question'].str.contains(kw, case=False, na=False) | \
                      filtered_df['answer'].str.contains(kw, case=False, na=False)
            or_mask = or_mask | kw_mask
        
        related_df = filtered_df[or_mask]
        
        if len(related_df) > 0:
            st.info(f"💡 혹시 이런 내용을 찾으시나요? (관련 유사 결과 {len(related_df)}건)")
            # 너무 많으면 상위 10개만 추천
            for i, row in related_df.head(10).iterrows():
                with st.expander(f"[{row['doc_type']}] {row['question']}"):
                    st.markdown(f"**📌 분류:** {row['category']}")
                    st.info(f"**💡 답변:**\n\n{row['answer']}")
                    st.caption(f"행정해석 근거: {row['reference']}")
                    
    # 5-5. 검색 결과가 있을 때 정상 출력
    else:
        for i, row in result_df.iterrows():
            expander_label = f"[{row['doc_type']}] {row['question']}"
            with st.expander(expander_label):
                st.markdown(f"**📌 분류:** {row['category']}")
                st.markdown(f"**📝 질문:** {row['question']}")
                st.info(f"**💡 답변:**\n\n{row['answer']}")
                st.caption(f"행정해석 근거: {row['reference']}")
                
                # [연관 질의 추천 기능] 같은 카테고리의 다른 질문 보여주기
                st.markdown("---")
                st.markdown("**🔗 이 질문과 연관된 질의회시 (같은 분류)**")
                
                same_category_df = df[(df['category'] == row['category']) & (df['id'] != row['id'])]
                if not same_category_df.empty:
                    # 최대 3개 무작위 추천
                    sample_size = min(3, len(same_category_df))
                    related_samples = same_category_df.sample(n=sample_size)
                    for _, rel_row in related_samples.iterrows():
                        st.markdown(f"- {rel_row['question']}")
                else:
                    st.markdown("- 연관된 다른 질의가 없습니다.")

# 6. 하단 정보 및 문의처
st.divider()
st.markdown("### 📞 도움이 필요하신가요?")
st.write("검색 결과가 정확하지 않거나 시스템 오류가 발생하면 아래 담당자에게 연락해 주세요.")

col1, col2 = st.columns([1, 2])
with col1:
    st.markdown("**담당자:** 안전팀 백찬주 대리")
    st.markdown("**전화:** 010-2528-5706")
with col2:
    st.link_button("📧 문의 메일 보내기", "mailto:여러분의이메일@company.com")

st.caption("📄 시스템 관련 문의사항은 언제든 환영합니다.")
