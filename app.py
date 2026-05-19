import streamlit as st
from gtts import gTTS
import os
import base64

# 1. 페이지 레이아웃 설정
st.set_page_config(page_title="🎙️ 나만의 원어민 발음기", layout="centered")

st.title("🎙️ 원어민 발음기 (TTS)")
st.caption("원하는 문장을 입력하고 원어민의 자연스러운 음성으로 들어보세요. API 키가 필요 없습니다!")

st.write("---")

# 2. 언어 선택 설정
lang_options = {
    "🇺🇸 영어 (English)": "en",
    "🇨🇳 중국어 (Chinese)": "zh-CN",
    "🇯🇵 일본어 (Japanese)": "ja",
    "🇰🇷 한국어 (Korean)": "ko"
}
selected_lang = st.selectbox("1. 읽어줄 언어를 선택하세요:", list(lang_options.keys()))
lang_code = lang_options[selected_lang]

# 3. 말하기 속도 설정 (학습용 느리게 듣기 추가)
speed_option = st.radio("2. 말하기 속도를 선택하세요:", ("보통 속도 (Normal)", "느린 속도 (Slow)"), horizontal=True)
is_slow = True if "느린" in speed_option else False

# 4. 텍스트 입력 창
text_to_speak = st.text_area("3. 읽어줄 문장을 입력하세요:", height=180, placeholder="여기에 문장을 입력하거나 복사해서 붙여넣으세요...")

# 🌟 음성 재생 함수
def play_audio(text, lang, slow):
    try:
        # gTTS 엔진으로 음성 파일 생성
        tts = gTTS(text=text, lang=lang, slow=slow)
        filename = "voice_output.mp3"
        tts.save(filename)
        
        # 생성된 오디오 파일을 읽어서 웹 화면에 플레이어로 재생
        with open(filename, "rb") as f:
            data = f.read()
            b64 = base64.b64encode(data).decode()
            # autoplay="true"를 넣어 버튼을 누르면 바로 소리가 나오게 설정
            audio_html = f'<audio controls autoplay="true" style="width: 100%;"><source src="data:audio/mp3;base64,{b64}" type="audio/mp3"></audio>'
            st.markdown(audio_html, unsafe_allow_html=True)
            
        # 임시 파일 삭제
        os.remove(filename)
    except Exception as e:
        st.error(f"⚠️ 음성을 생성하는 중 오류가 발생했습니다: {e}")

st.write("")

# 5. 실행 버튼
if st.button("🔊 원어민 발음으로 듣기", type="primary", use_container_width=True):
    if text_to_speak.strip():
        with st.spinner("목소리를 준비하고 있습니다..."):
            play_audio(text_to_speak.strip(), lang_code, is_slow)
    else:
        st.warning("먼저 읽어줄 문장을 입력해 주세요!")

