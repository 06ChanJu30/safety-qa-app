import streamlit as st
import pandas as pd
import json
import os

# 1. 페이지 기본 설정
st.set_page_config(page_title="안전보건 질의회시 검색기", page_icon="💡", layout="centered")

st.title("💡 안전보건 질의회시 통합 검색")
st.caption("폭염, 산안법, 중처법 등 각종 안전보건 질의회시 통합 검색 엔진")

current_dir = os.path.dirname(os.path.abspath(__file__))

# 2. 두 개의 JSON 파일 불러와서 자동으로 합치기 (핵심 기능 🌟)
@st.cache_data
def load_and_merge_data():
    all_data = []
    
    # 첫 번째: 기존 폭염 데이터 로드
    file1 = os.path.join(current_dir, "qa_database.json")
    if os.path.exists(file1):
        try:
            with open(file1, 'r', encoding='utf-8') as f:
                all_data.extend(json.load(f))
        except Exception as e:
            st.warning(f"⚠️ 폭염 데이터 로드 중 오류 발생: {e}")

    # 두 번째: 파이썬으로 새로 자동 추출한 대용량 데이터 로드
    file2 = os.path.join(current_dir, "integrated_qa.json")
    if os.path.exists(file2):
        try:
            with open(file2, 'r', encoding='utf-8') as f:
                all_data.extend(json.load(f))
        except Exception as e:
            st.warning(f"⚠️ 새 질의회시 데이터 로드 중 오류 발생: {e}")
            
    return pd.DataFrame(all_data)

df = load_and_merge_data()

# 에러 처리 (둘 다 못 불렀을 때)
if df.empty:
    st.error("데이터를 하나도 불러오지 못했습니다. 깃허브에 'qa_database.json' 또는 'integrated_qa.json' 파일이 잘 올라가 있는지 확인해주세요.")
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
        
    result_df = filtered_df[mask]
    
    st.subheader(f"총 {len(result_df)}건의 검색 결과가 있습니다.")
    st.divider()
    
    if len(result_df) == 0:
        st.warning("정확히 일치하는 내용이 없습니다.")
        
        # 합집합(OR) 유사 검색 (단어 중 하나라도 포함된 유사 결과 추천)
        or_mask = pd.Series([False] * len(filtered_df), index=filtered_df.index)
        for kw in keywords:
            kw_mask = filtered_df['question'].str.contains(kw, case=False, na=False) | \
                      filtered_df['answer'].str.contains(kw, case=False, na=False)
            or_mask = or_mask | kw_mask
        
        related_df = filtered_df[or_mask]
        
        if len(related_df) > 0:
            st.info(f"💡 혹시 이런 내용을 찾으시나요? (유사 결과 {len(related_df)}건 추천)")
            for i, row in related_df.head(10).iterrows():
                with st.expander(f"[{row.get('doc_type', '분류없음')}] {row.get('question', '제목없음')}"):
                    st.markdown(f"**📌 분류:** {row.get('category', '없음')}")
                    st.info(f"**💡 답변:**\n\n{row.get('answer', '내용없음')}")
                    st.caption(f"행정해석 근거: {row.get('reference', '없음')}")
    else:
        # 정상 검색 결과 출력
        for i, row in result_df.iterrows():
            expander_label = f"[{row.get('doc_type', '분류없음')}] {row.get('question', '제목없음')}"
            with st.expander(expander_label):
                st.markdown(f"**📌 분류:** {row.get('category', '없음')}")
                st.markdown(f"**📝 질문:** {row.get('question', '없음')}")
                st.info(f"**💡 답변:**\n\n{row.get('answer', '없음')}")
                st.caption(f"행정해석 근거: {row.get('reference', '없음')}")

# 6. 하단 정보 및 문의처
st.divider()
st.markdown("### 📞 도움이 필요하신가요?")
st.write("검색 결과가 정확하지 않거나 시스템 오류가 발생하면 아래 담당자에게 연락해 주세요.")

col1, col2 = st.columns([1, 2])
with col1:
    st.markdown("**담당자:** 안전팀 백찬주 대리")
    st.markdown("**전화:** 010-2528-5706")
with col2:
    st.link_button("📧 문의 메일 보내기", "mailto:이메일입력@company.com")

st.caption("📄 시스템 관련 문의사항은 언제든 환영합니다.")
