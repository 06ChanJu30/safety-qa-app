import streamlit as st
import pandas as pd
import json
import os

# 1. 페이지 기본 설정
st.set_page_config(page_title="안전보건 질의회시 검색기", page_icon="💡", layout="centered")

st.title("💡 안전보건 질의회시 통합 검색")
st.caption("폭염, 산안법, 중처법, 안전보건관리비 등 각종 안전보건 질의회시 통합 검색 엔진")

# 🌟 추가 기능: 캐시 초기화 버튼 (데이터가 꼬이거나 안 나올 때 누르면 한방에 해결)
if st.button("🔄 최신 데이터 불러오기 (검색 먹통 시 클릭!)"):
    st.cache_data.clear()
    st.rerun()

current_dir = os.path.dirname(os.path.abspath(__file__))

# 2. 모든 JSON 파일을 자동으로 찾아서 하나로 합치기
@st.cache_data
def load_and_merge_data():
    all_data = []
    
    # .json 파일 모두 긁어오기
    for filename in os.listdir(current_dir):
        if filename.endswith(".json"):
            file_path = os.path.join(current_dir, filename)
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    # 파일 형식 방어 로직 (리스트 형태인지 단일 형태인지)
                    if isinstance(data, list):
                        all_data.extend(data)
                    elif isinstance(data, dict):
                        all_data.append(data)
            except Exception as e:
                pass # 에러난 파일은 스킵하여 앱 멈춤 방지
                
    df = pd.DataFrame(all_data)
    
    if not df.empty:
        # 🌟 에러 방어 핵심 1: 필수 컬럼이 없으면 빈칸으로 강제 생성
        for col in ['doc_type', 'category', 'title', 'question', 'answer', 'reference']:
            if col not in df.columns:
                df[col] = ""
            
            # 🌟 에러 방어 핵심 2: 모든 데이터를 완벽한 문자로 강제 변환 (숫자 섞임, 빈칸으로 인한 뻗음 방지)
            df[col] = df[col].fillna("").astype(str)

        # 문서 이름 예쁘게 바꾸기
        df['doc_type'] = df['doc_type'].replace({
            '산업안전보건법 질의회시집': '📘 산업안전보건법 질의회시집(22.05)',
            '폭염 산업안전보건규칙': '☀️ 산업안전보건규칙 질의회시집_폭염 관련(26.05)',
            '중대재해처벌법 질의회시': '⚖️ 중대재해처벌법 질의회시집(23.05)',
            '중대재해처벌법': '⚖️ 중대재해처벌법 질의회시', 
            '안전보건관리비 질의회시': '💰 산업안전보건관리비 질의회시집(25.06)',
            '건설업 산업안전보건관리비': '💰 안전보건관리비 질의회시'
        })
        
    return df

df = load_and_merge_data()

# 데이터 로드 실패 처리
if df.empty:
    st.error("데이터베이스를 하나도 불러오지 못했습니다. 깃허브에 JSON 파일들이 잘 올라가 있는지 확인해주세요.")
    st.stop()

# 3. 검색 필터 생성
doc_types = ["전체"] + [d for d in list(df['doc_type'].unique()) if d.strip() != ""]
selected_doc = st.radio("📑 검색 대상 문서", doc_types, horizontal=True)

# 4. 검색창
query = st.text_input("🔍 검색어를 띄어쓰기로 여러 개 입력해보세요. (특수문자도 검색 가능)")

if query:
    if selected_doc != "전체":
        filtered_df = df[df['doc_type'] == selected_doc]
    else:
        filtered_df = df
        
    keywords = query.strip().split()
    mask = pd.Series([True] * len(filtered_df), index=filtered_df.index)
    
    try:
        # 교집합(AND) 검색
        for kw in keywords:
            kw_lower = kw.lower()
            # 🌟 에러 방어 핵심 3: regex=False를 통해 괄호()나 별표* 등 특수문자로 인한 검색기 폭파 완벽 차단!
            kw_mask = filtered_df['question'].str.lower().str.contains(kw_lower, regex=False, na=False) | \
                      filtered_df['answer'].str.lower().str.contains(kw_lower, regex=False, na=False)
            mask = mask & kw_mask
            
        result_df = filtered_df[mask]
        
        st.subheader(f"총 {len(result_df)}건의 검색 결과가 있습니다.")
        st.divider()
        
        if len(result_df) == 0:
            st.warning("정확히 일치하는 내용이 없습니다.")
            
            # 합집합(OR) 유사 검색 추천
            or_mask = pd.Series([False] * len(filtered_df), index=filtered_df.index)
            for kw in keywords:
                kw_lower = kw.lower()
                kw_mask = filtered_df['question'].str.lower().str.contains(kw_lower, regex=False, na=False) | \
                          filtered_df['answer'].str.lower().str.contains(kw_lower, regex=False, na=False)
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
                    
    except Exception as e:
        st.error("앗! 검색 중 문제가 발생했습니다. 검색어를 살짝 바꿔서 다시 시도해주세요.")

# 6. 하단 정보 및 문의처
st.divider()
st.markdown("### 📞 도움이 필요하신가요?")
st.write("검색 결과가 정확하지 않거나 시스템 오류가 발생하면 아래 담당자에게 연락해 주세요.")

col1, col2 = st.columns([1, 2])
with col1:
    st.markdown("**담당자:** 안전팀 백찬주 대리")
    st.markdown("**전화:** 010-2528-5706")

st.caption("📄 시스템 관련 문의사항은 언제든 환영합니다.")
