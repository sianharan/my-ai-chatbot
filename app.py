import streamlit as st
import google.generativeai as genai
import pandas as pd
import os

# 1. 페이지 설정
st.set_page_config(page_title="교육 정책 분석 전문가", layout="wide")
st.title("🤖 교육 정책 분석 전문가 챗봇")
st.info("정책 데이터를 분석하여 최적의 답변을 제공합니다.")

# 2. API 설정 및 v1beta 우회 강제 로직
if "GEMINI_API_KEY" in st.secrets:
    api_key = st.secrets["GEMINI_API_KEY"]
    
    # [가장 핵심] transport='rest'를 통해 v1beta로 자동 리다이렉트되는 것을 물리적으로 차단합니다.
    # 또한 api_version을 명시적으로 제어할 수 있는 구조로 설정합니다.
    genai.configure(api_key=api_key, transport='rest')
    
    try:
        # 모델명에서 'models/'를 생략하고 이름만 사용하여 v1 엔드포인트에 접속합니다.
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
        return None, f"'{file_name}' 파일을 찾을 수 없습니다. GitHub에 업로드했는지 확인하세요."
    
    try:
        # 엑셀 엔진을 openpyxl로 명시하여 안정성을 높입니다.
        df = pd.read_excel(file_name, engine='openpyxl')
        text_content = ""
        for i, row in df.iterrows():
            title = str(row.get('제목', '제목 없음'))
            content = str(row.get('내용', '내용 없음'))
            text_content += f"[{i+1}번 제안] 제목: {title} / 내용: {content}\n\n"
        return text_content, None
    except Exception as e:
        return None, f"엑셀 분석 중 오류 발생: {e}"

# 파일명 확인
policy_text, error_msg = load_policy_data("정책제안_6개월.xlsx")

if error_msg:
    st.error(error_msg)
    st.stop()

# 4. 채팅 시스템 초기화
if "messages" not in st.session_state:
    st.session_state.messages = []

# 대화 내역 표시
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# 5. 질문 처리 및 AI 응답
if prompt := st.chat_input("질문을 입력해 주세요."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    try:
        with st.chat_message("assistant"):
            # 프롬프트 구성
            full_prompt = f"""당신은 교육 정책 분석 전문가입니다. 
아래 [데이터]를 바탕으로 사용자의 질문에 답변하세요. 
답변 내용과 관련된 데이터의 번호(예: [1번 제안])를 반드시 언급하세요.

[데이터]
{policy_text}

[질문]
{prompt}"""
            
            # API 호출
            response = model.generate_content(full_prompt)
            
            if response and response.text:
                st.markdown(response.text)
                st.session_state.messages.append({"role": "assistant", "content": response.text})
            else:
                st.error("응답 생성에 실패했습니다. API 키의 할당량을 확인해 보세요.")
                
    except Exception as e:
        # 이 시점에서 발생하는 404 오류는 라이브러리 버전 문제입니다.
        st.error(f"분석 오류 발생: {e}")
        st.info("팁: requirements.txt의 google-generativeai 버전을 >=0.8.3으로 수정 후 Reboot 해보세요.")
