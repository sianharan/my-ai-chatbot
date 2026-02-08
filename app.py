많이 복잡하셨죠? 웹 배포를 위해 Secrets 기능을 완벽하게 지원하면서도, 아까 발생했던 따옴표 오류와 404 오류를 모두 해결한 최종 전체 코드를 작성해 드립니다.

이 코드를 복사해서 GitHub의 app.py에 통째로 덮어쓰기 하시면 됩니다.

🚀 최종 완성본: app.py 전체 코드
Python
import streamlit as st
import google.generativeai as genai
import pandas as pd

# 1. 웹 페이지 기본 설정
st.set_page_config(page_title="AI 정책 분석 전문가", layout="wide")
st.title("🤖 교육 정책 분석 전문가 챗봇")
st.info("데이터를 바탕으로 인공지능이 정책 제안을 분석합니다.")

# 2. Secrets에서 API 키 불러오기 및 설정
# Streamlit Cloud의 Secrets에 GEMINI_API_KEY가 저장되어 있어야 합니다.
if "GEMINI_API_KEY" in st.secrets:
    api_key = st.secrets["GEMINI_API_KEY"]
    genai.configure(api_key=api_key)
    # 404 오류 방지를 위해 경로 없이 모델 이름만 사용
    model = genai.GenerativeModel('gemini-1.5-flash')
else:
    st.error("⚠️ Secrets 설정에서 'GEMINI_API_KEY'를 등록해주세요!")
    st.stop() # 키가 없으면 여기서 실행 중단

# 3. 데이터 로드 함수 (캐시 적용으로 속도 향상)
@st.cache_data
def get_policy_data(file_name):
    try:
        df = pd.read_excel(file_name)
        text_data = ""
        for i, row in df.iterrows():
            # 따옴표 오류를 방지하기 위해 안전하게 작성된 코드
            title = str(row['제목']) if '제목' in df.columns else "제목없음"
            content = str(row['내용']) if '내용' in df.columns else "내용없음"
            text_data += f"[{i+1}번 제안] 제목: {title} / 내용: {content}\n\n"
        return text_data
    except Exception as e:
        return f"파일을 읽는 중 오류가 발생했습니다: {e}"

# 데이터 가져오기 (파일명이 정확해야 합니다)
all_policies = get_policy_data("정책제안_6개월.xlsx")

# 4. 채팅 메시지 저장 공간 초기화
if "messages" not in st.session_state:
    st.session_state.messages = []

# 5. 기존 대화 내용 화면에 표시
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# 6. 채팅 입력창 및 AI 분석 로직
if prompt := st.chat_input("정책에 대해 궁금한 점을 물어보세요!"):
    # 유저 메시지 표시 및 저장
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # AI 응답 생성
    try:
        with st.chat_message("assistant"):
            # 전문가 페르소나와 데이터를 포함한 프롬프트
            full_command = f"""당신은 15년 차 교육 정책 분석 전문가입니다. 
아래의 [정책 데이터]를 정밀하게 분석하여 질문에 답변하세요.
답변 시 반드시 관련된 정책 번호(예: [3번 제안])를 포함하세요.

[정책 데이터]
{all_policies}

[질문]
{prompt}"""
            
            # AI 실행
            response = model.generate_content(full_command)
            st.markdown(response.text)
            
            # 응답 저장
            st.session_state.messages.append({"role": "assistant", "content": response.text})
            
    except Exception as e:
        st.error(f"분석 중 오류가 발생했습니다: {e}")
        st.info("💡 해결 방법: requirements.txt 파일에 google-generativeai>=0.8.3 가 있는지 확인해 보세요.")
