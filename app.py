import streamlit as st
import google.generativeai as genai
import pandas as pd

# 페이지 설정
st.set_page_config(page_title="AI 정책 분석 전문가", layout="wide")

st.title("🤖 교육 정책 분석 전문가 챗봇")
st.info("엑셀 데이터를 바탕으로 인공지능이 정책 제안을 분석해 드립니다.")

# 사이드바 설정
st.sidebar.header("설정")
user_api_key = st.sidebar.text_input("Gemini API Key 입력", type="password")

# 엑셀 파일 로드 (사전에 GitHub에 올린 파일명과 일치해야 함)
file_path = "정책제안_6개월.xlsx"

@st.cache_data
def load_data(path):
    try:
        df = pd.read_excel(path)
        all_text = ""
        for i, row in df.iterrows():
            title = str(row['제목'])
            content = str(row['내용'])
            # 아래 줄이 오류가 났던 부분입니다. 따옴표 짝을 완벽히 맞췄습니다.
            all_text += f"[{i+1}번 제안] 제목: {title} / 내용: {content}\n\n"
        return all_text
    except Exception as e:
        return f"파일 로드 오류: {e}"

all_policies = load_data(file_path)

# 채팅 인터페이스
if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("정책에 대해 궁금한 점을 물어보세요!"):
    if not user_api_key:
        st.error("사이드바에 Gemini API Key를 먼저 입력해 주세요!")
    else:
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        try:
            genai.configure(api_key=user_api_key)
            model = genai.GenerativeModel('gemini-1.5-flash')
            
            # AI에게 줄 명령 생성
            full_prompt = f"너는 정책 분석 전문가야. 다음 데이터를 바탕으로 질문에 답해줘.\n\n[데이터]\n{all_policies}\n\n[질문]\n{prompt}"
            
            with st.chat_message("assistant"):
                response = model.generate_content(full_prompt)
                st.markdown(response.text)
                st.session_state.messages.append({"role": "assistant", "content": response.text})
        except Exception as e:
            st.error(f"분석 중 오류가 발생했습니다: {e}")
