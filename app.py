import streamlit as st
import google.generativeai as genai
import pandas as pd
import os

# 1. 페이지 설정
st.set_page_config(page_title="교육 정책 분석 전문가", layout="wide")
st.title("🤖 교육 정책 분석 전문가 챗봇")
st.info("시스템이 사용 가능한 최적의 모델을 자동으로 탐색하여 연결합니다.")

# 2. API 설정 및 모델 자동 탐색 로직
if "GEMINI_API_KEY" in st.secrets:
    api_key = st.secrets["GEMINI_API_KEY"]
    
    # [핵심] v1beta 경로 문제를 피하기 위해 정식 버전(v1) 통신 규격 강제 설정
    genai.configure(api_key=api_key, transport='rest')
    
    try:
        # 현재 API 키로 접근 가능한 모델 목록 가져오기
        available_models = []
        for m in genai.list_models():
            # 채팅(콘텐츠 생성)이 가능한 모델만 선별
            if 'generateContent' in m.supported_generation_methods:
                available_models.append(m.name)
        
        if not available_models:
            st.error("❌ 사용 가능한 모델을 찾을 수 없습니다. API 키 권한을 확인해 주세요.")
            st.stop()
            
        # 우선순위에 따라 모델 자동 선택 (1.5-flash -> 1.5-pro -> 리스트의 첫 번째 모델)
        selected_model_name = next((m for m in available_models if 'gemini-1.5-flash' in m), 
                              next((m for m in available_models if 'gemini-1.5-pro' in m), 
                              available_models[0]))
        
        # 선택된 모델로 연결
        model = genai.GenerativeModel(selected_model_name)
        st.success(f"✅ 연결된 모델: `{selected_model_name}`")
        
    except Exception as e:
        st.error(f"⚠️ 모델 리스트 탐색 중 오류 발생: {e}")
        st.stop()
else:
    st.error("⚠️ Streamlit Secrets에 'GEMINI_API_KEY'를 등록해 주세요!")
    st.stop()

# 3. 데이터 로드 (캐싱 적용)
@st.cache_data
def load_policy_data(file_name):
    if not os.path.exists(file_name):
        return None, f"'{file_name}' 파일을 찾을 수 없습니다."
    
    try:
        # 엑셀 엔진 명시
        df = pd.read_excel(file_name, engine='openpyxl')
        text_content = ""
        for i, row in df.iterrows():
            title = str(row.get('제목', '제목 없음'))
            content = str(row.get('내용', '내용 없음'))
            text_content += f"[{i+1}번 제안] 제목: {title} / 내용: {content}\n\n"
        return text_content, None
    except Exception as e:
        return None, f"데이터 분석 중 오류 발생: {e}"

# 엑셀 파일 로드
policy_text, error_msg = load_policy_data("정책제안_6개월.xlsx")

if error_msg:
    st.error(error_msg)
    st.stop()

# 4. 채팅 인터페이스 초기화
if "messages" not in st.session_state:
    st.session_state.messages = []

# 대화 기록 표시
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# 5. 질문 처리 및 응답 생성
if prompt := st.chat_input("정책에 대해 질문해 보세요."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    try:
        with st.chat_message("assistant"):
            full_prompt = f"""당신은 교육 정책 분석 전문가입니다. 
아래 제공된 [데이터]만을 근거로 답변하세요. 
답변 시 관련된 제안의 번호(예: [1번 제안])를 반드시 포함하세요.

[데이터]
{policy_text}

[질문]
{prompt}"""
            
            # 자동 탐색된 모델을 사용하여 응답 생성
            response = model.generate_content(full_prompt)
            
            if response and response.text:
                st.markdown(response.text)
                st.session_state.messages.append({"role": "assistant", "content": response.text})
            else:
                st.warning("AI가 응답을 생성하지 못했습니다. 질문을 다시 입력해 보세요.")
                
    except Exception as e:
        st.error(f"분석 중 오류 발생: {e}")
        st.info("팁: API 키 권한이 충분한지, 혹은 모델 주소가 v1beta로 강제 전환되고 있지 않은지 확인이 필요합니다.")
