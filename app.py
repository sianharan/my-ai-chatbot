import streamlit as st
import google.generativeai as genai
import pandas as pd
import os

# 1. 페이지 설정
st.set_page_config(page_title="교육 정책 분석 전문가", layout="wide")
st.title("🤖 교육 정책 분석 전문가 챗봇")
st.info("엑셀 데이터를 기반으로 정책 제안을 정밀 분석합니다.")

# 2. Secrets 보안 설정
if "GEMINI_API_KEY" in st.secrets:
    api_key = st.secrets["GEMINI_API_KEY"]
    
    # [가장 중요한 수정] 
    # transport='rest'를 설정하여 HTTP 통신 방식으로 강제하고 최신 라이브러리 규격을 따릅니다.
    genai.configure(api_key=api_key, transport='rest')
    
    try:
        # 모델 객체 생성 - 버전 충돌 방지를 위해 이름만 정확히 기입합니다.
        model = genai.GenerativeModel('gemini-1.5-flash')
    except Exception as e:
        st.error(f"모델 설정 중 오류 발생: {e}")
else:
    st.error("⚠️ Streamlit Secrets에 'GEMINI_API_KEY'를 등록해 주세요!")
    st.stop()

# 3. 데이터 로드 (캐싱 적용)
@st.cache_data
def load_policy_data(file_name):
    if not os.path.exists(file_name):
        return None, f"'{file_name}' 파일을 찾을 수 없습니다. GitHub 업로드 여부를 확인하세요."
    
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

# 엑셀 파일명 (GitHub에 올린 파일명과 일치해야 함)
policy_text, error_msg = load_policy_data("정책제안_6개월.xlsx")

if error_msg:
    st.error(error_msg)
    st.stop()

# 4. 채팅 인터페이스 관리
if "messages" not in st.session_state:
    st.session_state.messages = []

# 대화 기록 표시
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# 5. 유저 입력 및 AI 응답 처리
if prompt := st.chat_input("정책에 대해 궁금한 점을 질문해 보세요."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    try:
        with st.chat_message("assistant"):
            # 프롬프트 구성
            full_prompt = f"""당신은 교육 정책 분석 전문가입니다. 
제공된 [데이터]만을 근거로 사용자의 질문에 답변하세요. 
답변 시 관련된 제안의 번호(예: [1번 제안])를 반드시 언급하세요.

[데이터]
{policy_text}

[질문]
{prompt}"""
            
            # AI 답변 생성
            response = model.generate_content(full_prompt)
            
            if response and response.text:
                st.markdown(response.text)
                st.session_state.messages.append({"role": "assistant", "content": response.text})
            else:
                st.error("AI로부터 응답을 받지 못했습니다. API 키나 모델 설정을 확인해 주세요.")
            
    except Exception as e:
        st.error(f"분석 중 오류가 발생했습니다: {e}")
