import streamlit as st
from deep_translator import GoogleTranslator
from gtts import gTTS
import os
import base64
import sqlite3
import re
from datetime import datetime
import jieba # 중국어 단어 추출기
from pypinyin import pinyin, Style
import pykakasi # 일본어 단어 추출 및 발음기

# 1. 화면 설정
st.set_page_config(page_title="무제한 로컬 어학기", layout="wide")

# 2. 데이터베이스 세팅
def init_db():
    conn = sqlite3.connect('my_sentences_local.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS sentences_local
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  date_added TEXT, ko TEXT, en TEXT, zh TEXT, zh_pron TEXT, zh_desc TEXT, 
                  ja TEXT, ja_pron TEXT, ja_desc TEXT, last_tested TEXT)''')
    conn.commit()
    conn.close()

init_db()

# 3. 음성 재생 함수
def speak(text, lang):
    try:
        tts = gTTS(text=text, lang=lang)
        filename = f"voice_{lang}.mp3"
        tts.save(filename)
        with open(filename, "rb") as f:
            data = f.read()
            b64 = base64.b64encode(data).decode()
            md = f'<audio controls autoplay="true"><source src="data:audio/mp3;base64,{b64}" type="audio/mp3"></audio>'
            st.markdown(md, unsafe_allow_html=True)
        os.remove(filename)
    except: pass

# 4. 로컬 분석 함수 (AI 없이 단어 뽑기)
def analyze_chinese(text):
    # 단어 분리
    words = jieba.lcut(text)
    unique_words = [w for w in words if len(w) > 1] # 1글자(조사 등) 제외하고 추출
    desc = "추출 단어: " + ", ".join(unique_words)
    pron = " ".join([p[0] for p in pinyin(text, style=Style.TONE)])
    return pron, desc

def analyze_japanese(text):
    kks = pykakasi.kakasi()
    result = kks.convert(text)
    pron = " ".join([item['hira'] for item in result])
    # 한자가 포함된 단어들 위주로 추출
    unique_words = [item['orig'] for item in result if item['orig'] != item['hira']]
    desc = "추출 단어(한자): " + ", ".join(list(set(unique_words)))
    return pron, desc

# 기억력 세팅
if 'scenario_data' not in st.session_state:
    st.session_state.scenario_data = []
if 'test_sentences' not in st.session_state:
    st.session_state.test_sentences = []

st.title("🚀 무제한 로컬 어학 학습기")
st.caption("AI 토큰 제한 없이 무제한으로 문장을 분석하고 저장합니다.")

tab1, tab2, tab3 = st.tabs(["📝 오늘의 학습", "📚 내 보관함", "🎯 작문 테스트"])

# ==========================================
# [탭 1] 오늘의 학습
# ==========================================
with tab1:
    input_text = st.text_area("공부할 한국어 문장을 입력하세요:", height=100)

    if st.button("분석 시작 (토큰 소모 없음)", type="primary"):
        if input_text:
            raw_sentences = re.split(r'(?<=[.!?])\s+|\n+', input_text)
            sentences = [s.strip() for s in raw_sentences if s.strip()]
            
            results = []
            with st.spinner("로컬 엔진으로 분석 중..."):
                for s in sentences:
                    # 안전망: 문장이 너무 짧거나 특수문자만 있으면 건너뛰기
                    if len(s) < 2: 
                        continue
                        
                    try:
                        # 번역 (deep-translator 사용)
                        en = GoogleTranslator(source='ko', target='en').translate(s)
                        zh = GoogleTranslator(source='ko', target='zh-CN').translate(s)
                        ja = GoogleTranslator(source='ko', target='ja').translate(s)
                        
                        zh_pron, zh_desc = analyze_chinese(zh)
                        ja_pron, ja_desc = analyze_japanese(ja)
                        
                        results.append({
                            'ko': s, 'en': en, 'zh': zh, 'zh_pron': zh_pron, 'zh_desc': zh_desc,
                            'ja': ja, 'ja_pron': ja_pron, 'ja_desc': ja_desc
                        })
                    except Exception as e:
                        # 번역 실패 시 앱이 튕기지 않고 경고창만 띄우고 넘어감
                        st.warning(f"⚠️ '{s}' 문장 번역 중 오류가 발생해 건너뛰었습니다.")
                        continue
            st.session_state.scenario_data = results

    if st.session_state.scenario_data:
        for i, data in enumerate(st.session_state.scenario_data):
            st.markdown(f"### {data['ko']}")
            col1, col2, col3 = st.columns(3)
            with col1:
                st.success("🇺🇸 영어")
                st.info(data['en'])
                if st.button("🔊", key=f"en_{i}"): speak(data['en'], 'en')
            with col2:
                st.success("🇨🇳 중국어")
                st.info(f"{data['zh']}\n\n({data['zh_pron']})")
                st.caption(data['zh_desc'])
                if st.button("🔊", key=f"zh_{i}"): speak(data['zh'], 'zh-CN')
            with col3:
                st.success("🇯🇵 일본어")
                st.info(f"{data['ja']}\n\n({data['ja_pron']})")
                st.caption(data['ja_desc'])
                if st.button("🔊", key=f"ja_{i}"): speak(data['ja'], 'ja')
            
            if st.button("💾 저장", key=f"save_{i}"):
                conn = sqlite3.connect('my_sentences_local.db')
                c = conn.cursor()
                now = datetime.now().strftime("%Y-%m-%d %H:%M")
                c.execute("INSERT INTO sentences_local (date_added, ko, en, zh, zh_pron, zh_desc, ja, ja_pron, ja_desc, last_tested) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", 
                          (now, data['ko'], data['en'], data['zh'], data['zh_pron'], data['zh_desc'], data['ja'], data['ja_pron'], data['ja_desc'], '0000-00-00 00:00')) 
                conn.commit()
                conn.close()
                st.toast("✅ 저장 완료!")
            st.write("---")

# ==========================================
# [탭 2] 내 보관함 / [탭 3] 테스트는 기존 로직과 동일 (생략/유지)
# ==========================================
# (보관함과 테스트 코드는 기존 코드의 데이터베이스 테이블 이름만 sentences_local로 바꿔서 사용하시면 됩니다.)
