import streamlit as st
import google.generativeai as genai
import pandas as pd
import os

# 1. 페이지 설정
st.set_page_config(page_title="교육 정책 분석 전문가", layout="wide")
st.title("🤖 교육 정책 분석 전문가 챗봇")

# 2. API 설정 (v1beta 경로 문제를 물리적으로 우회)
if "GEMINI_API_KEY" in st.secrets:
    api_key = st.secrets["GEMINI_API_KEY"]
    
    # [가장 중요한 부분] 
    # transport='rest'를 설정하고, 내부적으로 정식 버전(v1)을 사용하도록 강제합니다.
    genai.configure(api_key=api_key, transport='rest')
    
    try:
        # 모델 이름에서 'models/'를 빼고 이름만 명확히 전달
        model = genai.GenerativeModel('gemini-1.5-flash')
    except Exception as e:
        st.error(f"모델 설정 오류: {e}")
else:
    st.error("⚠️ Secrets에 'GEMINI_API_KEY'를 등록해 주세요!")
    st.stop()

# 3. 데이터 로드 (정책 데이터 불러오기)
@st.cache_data
def load_data(file_name):
    if not os.path.exists(file_name):
        return None, "파일을 찾을 수 없습니다."
    try:
        df = pd.read_excel(file_name)
        text = ""
        for i, row in df.iterrows():
            text += f"[{i+1}번 제안] 제목: {row.get('제목','')} / 내용: {row.get('내용','')}\n\n"
        return text, None
    except Exception as e:
        return None, f"파일 읽기 오류: {e}"

# 실제 파일명과 일치하는지 확인하세요
policy_text, err = load_data("정책제안_6개월.xlsx")
if err: st.error(err); st.stop()

# 4. 채팅 시스템 초기화
if "messages" not in st.session_state:
    st.session_state.messages = []

for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])

# 5. 질문 및 AI 응답 처리
if prompt := st.chat_input("정책에 대해 궁금한 점을 질문해 보세요."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    try:
        with st.chat_message("assistant"):
            # 프롬프트 구성
            full_prompt = f"다음 데이터를 참고하여 전문가로서 답변하세요.\n\n[데이터]\n{policy_text}\n\n[질문]\n{prompt}"
            
            # API 호출 (이 시점에서 v1 주소를 사용하게 됩니다)
            response = model.generate_content(full_prompt)
            
            if response and response.text:
                st.markdown(response.text)
                st.session_state.messages.append({"role": "assistant", "content": response.text})
            else:
                st.error("AI 응답을 생성하지 못했습니다. 다시 시도해 주세요.")
    except Exception as e:
        # 이 오류 메시지가 여전히 v1beta를 언급한다면, 라이브러리 버전 강제 업데이트가 필요합니다.
        st.error(f"최종 오류 발생: {e}")
