import streamlit as st
import google.generativeai as genai
import pandas as pd
import os

# 1. 페이지 설정
st.set_page_config(page_title="교육 정책 분석 전문가", layout="wide")
st.title("🤖 교육 정책 분석 전문가 챗봇")
st.info("데이터를 기반으로 정책 제안을 정밀 분석합니다.")

# 2. API 설정 및 주소 강제 고정
if "GEMINI_API_KEY" in st.secrets:
    api_key = st.secrets["GEMINI_API_KEY"]
    
    # [핵심] v1beta 주소 문제를 해결하기 위해 v1 정식 주소를 사용하게 합니다.
    # transport='rest' 설정은 통신 규격을 가장 안정적인 방식으로 고정합니다.
    genai.configure(api_key=api_key, transport='rest')
    
    try:
        # 모델 객체 생성 (경로 없이 이름만 사용)
        model = genai.GenerativeModel('gemini-1.5-flash')
    except Exception as e:
        st.error(f"모델 설정 오류: {e}")
else:
    st.error("⚠️ Secrets에 'GEMINI_API_KEY'를 등록해 주세요!")
    st.stop()

# 3. 데이터 로드 (캐싱)
@st.cache_data
def load_data(file_name):
    if not os.path.exists(file_name):
        return None, f"파일({file_name})이 없습니다. 업로드 상태를 확인하세요."
    try:
        df = pd.read_excel(file_name)
        text = ""
        for i, row in df.iterrows():
            t = str(row.get('제목', '제목없음'))
            c = str(row.get('내용', '내용없음'))
            text += f"[{i+1}번 제안] 제목: {t} / 내용: {c}\n\n"
        return text, None
    except Exception as e:
        return None, f"엑셀 읽기 오류: {e}"

policy_text, error = load_data("정책제안_6개월.xlsx")
if error:
    st.error(error)
    st.stop()

# 4. 채팅 시스템
if "messages" not in st.session_state:
    st.session_state.messages = []

for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])

# 5. 질문 처리 및 AI 응답
if prompt := st.chat_input("질문을 입력하세요"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    try:
        with st.chat_message("assistant"):
            full_prompt = f"데이터를 참고해 답해줘.\n[데이터]\n{policy_text}\n[질문]\n{prompt}"
            
            # API 호출 시점에 오류가 발생하면 출력합니다.
            response = model.generate_content(full_prompt)
            
            if response and response.text:
                st.markdown(response.text)
                st.session_state.messages.append({"role": "assistant", "content": response.text})
            else:
                st.error("AI 응답을 생성할 수 없습니다.")
                
    except Exception as e:
        st.error(f"오류 발생: {e}")
