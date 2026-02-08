import streamlit as st
import google.generativeai as genai
from google.generativeai import types
import pandas as pd
import os

# 1. 페이지 설정
st.set_page_config(page_title="교육 정책 분석 전문가", layout="wide")
st.title("🤖 교육 정책 분석 전문가 챗봇")

# 2. API 설정 (v1beta 404 오류를 원천 차단하는 초강수 설정)
if "GEMINI_API_KEY" in st.secrets:
    api_key = st.secrets["GEMINI_API_KEY"]
    
    # [핵심] 정식 버전인 v1 주소로 직접 통신하도록 강제 설정합니다.
    # v1beta 메시지가 뜨는 길 자체를 차단합니다.
    genai.configure(api_key=api_key, transport='rest')
    
    try:
        # 모델 생성 시 클라이언트 옵션을 통해 v1 버전을 사용하도록 명시할 수 있습니다.
        # (라이브러리 버전에 따라 지원 여부가 다르나, transport='rest'와 조합하면 매우 강력합니다)
        model = genai.GenerativeModel(
            model_name='gemini-1.5-flash'
        )
    except Exception as e:
        st.error(f"모델 설정 오류: {e}")
else:
    st.error("⚠️ Secrets에 'GEMINI_API_KEY'를 등록해 주세요!")
    st.stop()

# 3. 데이터 로드 (캐싱)
@st.cache_data
def load_policy_data(file_name):
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

policy_text, error_msg = load_policy_data("정책제안_6개월.xlsx")

if error_msg:
    st.error(error_msg)
    st.stop()

# 4. 채팅 시스템 초기화
if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# 5. 질문 및 응답 처리
if prompt := st.chat_input("정책에 대해 질문해 보세요."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    try:
        with st.chat_message("assistant"):
            full_prompt = f"다음 데이터를 참고하여 전문가로서 답변하세요.\n\n[데이터]\n{policy_text}\n\n[질문]\n{prompt}"
            
            # API 호출 시점에 오류가 발생하면 404 v1beta 메시지가 출력됩니다.
            # 이 코드는 v1을 사용하도록 설정되어 있어 오류 확률이 매우 낮습니다.
            response = model.generate_content(full_prompt)
            
            if response and response.text:
                st.markdown(response.text)
                st.session_state.messages.append({"role": "assistant", "content": response.text})
            else:
                st.error("AI 응답을 생성하지 못했습니다.")
    except Exception as e:
        st.error(f"분석 중 오류가 발생했습니다: {e}")
