import streamlit as st
import google.generativeai as genai
import pandas as pd
import os

# 1. 페이지 설정
st.set_page_config(page_title="교육 정책 분석 전문가", layout="wide")
st.title("🤖 교육 정책 분석 전문가 챗봇")

# 2. API 설정 및 v1beta 경로 우회 (핵심 설정)
if "GEMINI_API_KEY" in st.secrets:
    api_key = st.secrets["GEMINI_API_KEY"]
    
    # [가장 중요한 부분] transport='rest'를 사용하여 v1beta 접속 오류를 차단합니다.
    genai.configure(api_key=api_key, transport='rest')
    
    try:
        # 모델 이름 앞에 'models/'를 절대 붙이지 마세요.
        model = genai.GenerativeModel('gemini-1.5-flash')
    except Exception as e:
        st.error(f"모델 설정 오류: {e}")
else:
    st.error("⚠️ Secrets에 'GEMINI_API_KEY'를 등록해 주세요!")
    st.stop()

# 3. 데이터 로드 (캐싱 적용)
@st.cache_data
def load_data(file_name):
    if not os.path.exists(file_name):
        return None, f"'{file_name}' 파일을 찾을 수 없습니다."
    try:
        df = pd.read_excel(file_name)
        text_content = ""
        for i, row in df.iterrows():
            title = str(row.get('제목', '제목 없음'))
            content = str(row.get('내용', '내용 없음'))
            text_content += f"[{i+1}번 제안] 제목: {title} / 내용: {content}\n\n"
        return text_content, None
    except Exception as e:
        return None, f"데이터 분석 중 오류 발생: {e}"

# 파일명을 정확히 확인하세요.
policy_text, error_msg = load_data("정책제안_6개월.xlsx")

if error_msg:
    st.error(error_msg)
    st.stop()

# 4. 채팅 시스템 초기화
if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# 5. 유저 입력 및 AI 응답 처리
if prompt := st.chat_input("정책에 대해 질문해 보세요."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    try:
        with st.chat_message("assistant"):
            full_prompt = f"데이터를 참고하여 전문가로서 답변하세요.\n\n[데이터]\n{policy_text}\n\n[질문]\n{prompt}"
            
            # 여기서 v1 주소를 통해 Gemini와 연결을 시도합니다.
            response = model.generate_content(full_prompt)
            
            if response and response.text:
                st.markdown(response.text)
                st.session_state.messages.append({"role": "assistant", "content": response.text})
            else:
                st.error("AI 응답을 생성하지 못했습니다.")
    except Exception as e:
        st.error(f"분석 중 오류 발생: {e}")
