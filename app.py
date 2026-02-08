import streamlit as st
import google.generativeai as genai
import pandas as pd
import os

# 1. 페이지 설정
st.set_page_config(page_title="교육 정책 분석 전문가", layout="wide")
st.title("🤖 교육 정책 분석 전문가 챗봇")

# 2. API 설정 (404 오류 원천 차단 로직)
if "GEMINI_API_KEY" in st.secrets:
    api_key = st.secrets["GEMINI_API_KEY"]
    
    # [핵심] transport='rest'를 사용하여 v1beta 주소 체계 문제를 우회합니다.
    genai.configure(api_key=api_key, transport='rest')
    
    try:
        # 모델 이름에서 'models/'를 제거하고 순수 이름만 사용
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
        return None, "엑셀 파일을 찾을 수 없습니다."
    try:
        df = pd.read_excel(file_name)
        text = ""
        for i, row in df.iterrows():
            text += f"[{i+1}번 제안] 제목: {row.get('제목','')} / 내용: {row.get('내용','')}\n\n"
        return text, None
    except Exception as e:
        return None, f"파일 읽기 오류: {e}"

policy_text, err = load_data("정책제안_6개월.xlsx")
if err: st.error(err); st.stop()

# 4. 채팅 시스템
if "messages" not in st.session_state:
    st.session_state.messages = []

for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])

# 5. 질문 및 응답
if prompt := st.chat_input("질문을 입력하세요"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    try:
        with st.chat_message("assistant"):
            # 정교한 프롬프트 주입
            full_prompt = f"데이터를 참고해 답해줘.\n[데이터]\n{policy_text}\n[질문]\n{prompt}"
            
            # API 호출
            response = model.generate_content(full_prompt)
            
            if response and response.text:
                st.markdown(response.text)
                st.session_state.messages.append({"role": "assistant", "content": response.text})
            else:
                st.error("AI 응답 생성 실패")
    except Exception as e:
        st.error(f"최종 오류 발생: {e}")
        st.info("해결책: Streamlit Cloud 설정에서 'Reboot App'을 반드시 실행해 주세요.")
