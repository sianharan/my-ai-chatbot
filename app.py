
import streamlit as st
import google.generativeai as genai
import pandas as pd

# API 키 설정 (보안을 위해 환경 변수 사용을 권장하지만, 예시를 위해 직접 입력)
MY_API_KEY = st.secrets["GEMINI_API_KEY"]
genai.configure(api_key=MY_API_KEY)

st.title('정책 제안 챗봇')

# 'chat_history'가 세션 상태에 없으면 빈 리스트로 초기화합니다.
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []

# 데이터 로드 및 전처리 (Streamlit 앱이 시작될 때 한 번만 실행)
@st.cache_data
def load_data_and_model():
    file_name = '정책제안_6개월.xlsx'
    try:
        df = pd.read_excel(file_name)
        all_policies = ""
        for i, row in df.iterrows():
            all_policies += f"[{i+1}번 제안] 제목: {str(row['제목'])} / 내용: {str(row['내용'])}\n\n"

"
        model = genai.GenerativeModel('gemini-flash-latest')
        return all_policies, model
    except Exception as e:
        st.error(f"❌ 데이터 또는 모델 로드 오류 발생: {e}")
        return None, None

all_policies, model = load_data_and_model()

# 대화 기록 표시
for message in st.session_state.chat_history:
    with st.chat_message(message['role']):
        st.write(message['content'])

# 사용자 입력 필드 생성
prompt = st.chat_input('정책 제안에 대해 궁금한 점을 질문해주세요.')

if prompt and all_policies and model: # 사용자가 메시지를 입력했고, 데이터와 모델이 준비되었을 경우
    st.session_state.chat_history.append({'role': 'user', 'content': prompt})
    with st.chat_message('user'):
        st.write(prompt)

    # Gemini 모델을 사용하여 응답 생성
    with st.chat_message('assistant'):
        with st.spinner('AI 정책 분석관이 답변을 생성 중입니다...'):
            # 기존에 로드된 all_policies 데이터를 활용하여 프롬프트 구성
            context_prompt = f"""당신은 교육 정책 전문가입니다. 다음 정책 제안 데이터를 기반으로 사용자의 질문에 답변하세요.
            가능하다면 [n번 제안] 형식을 사용하여 특정 제안을 언급해주세요.

            [정책 제안 데이터]
            {all_policies}

            [사용자 질문]
            {prompt}"""

            try:
                response = model.generate_content(context_prompt)
                ai_response = response.text
                st.write(ai_response)
                st.session_state.chat_history.append({'role': 'assistant', 'content': ai_response})
            except Exception as e:
                st.error(f"❌ AI 응답 생성 실패: {e}")
                st.session_state.chat_history.append({'role': 'assistant', 'content': '죄송합니다. 답변을 생성하는 데 문제가 발생했습니다.'})
elif prompt and (not all_policies or not model):
    st.error("❌ 챗봇이 아직 준비되지 않았습니다. 데이터를 로드하거나 모델을 초기화하는 데 문제가 발생했을 수 있습니다.")
    st.session_state.chat_history.append({'role': 'assistant', 'content': '죄송합니다. 챗봇이 준비되지 않아 답변을 생성할 수 없습니다.'})
