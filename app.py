import streamlit as st
import google.generativeai as genai
from gtts import gTTS
import os
import base64
import sqlite3
import re
from datetime import datetime
import json

# 🌟 1. AI 열쇠 설정 (본인의 API 키로 반드시 변경하세요!)
GEMINI_API_KEY = "AIzaSyD3Dgr_nkl6X76Mds5rUhzkwwBowZZ57Ko"
genai.configure(api_key=GEMINI_API_KEY)

# AI 두뇌 세팅 (항상 정리된 JSON 양식으로만 대답하도록 강제 훈련)
model = genai.GenerativeModel('gemini-2.5-flash', 
                              generation_config={"response_mime_type": "application/json"})

st.set_page_config(page_title="나만의 AI 어학기", layout="wide")

# 2. 데이터베이스 초기 세팅 (문법 설명 칸이 추가된 새로운 창고 'sentences_v2' 생성)
def init_db():
    conn = sqlite3.connect('my_sentences.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS sentences_v2
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  date_added TEXT, 
                  ko TEXT, en TEXT, zh TEXT, zh_pron TEXT, zh_desc TEXT, 
                  ja TEXT, ja_pron TEXT, ja_desc TEXT,
                  last_tested TEXT)''')
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
    except Exception as e:
        pass

# 4. 기억력 세팅
if 'scenario_data' not in st.session_state:
    st.session_state.scenario_data = []
if 'test_sentences' not in st.session_state:
    st.session_state.test_sentences = []

st.title("🧠 1:1 맞춤형 AI 어학 튜터")

tab1, tab2, tab3 = st.tabs(["📝 오늘의 시나리오", "📚 내 문장 보관함", "🎯 작문 테스트"])

# ==========================================
# [탭 1] 오늘의 시나리오 (AI 분석)
# ==========================================
with tab1:
    input_text = st.text_area("공부할 시나리오를 입력하세요:", height=100)

    if st.button("AI 분석 및 학습 시작", type="primary"):
        if input_text:
            raw_sentences = re.split(r'(?<=[.!?])\s+|\n+', input_text)
            sentences = [s.strip() for s in raw_sentences if s.strip()]
            
            results = []
            with st.spinner("AI 선생님이 문장을 꼼꼼하게 분석 중입니다..."):
                for s in sentences:
                    # 🌟 AI에게 내리는 프롬프트(명령어)
                    prompt = f"""
                    다음 한국어 문장을 영어, 중국어(간체), 일본어로 번역하고 분석해줘.
                    특히 중국어는 주요 단어와 핵심 문장 구조 이야기 해주고, 일본어는 중요 한자의 뜻과 읽는 법(히라가나로)을 정리해줘.
                    가독성 좋게 한국어로 답해줘.

                    문장: "{s}"
                    
                    반드시 아래 JSON 형식으로만 답해줘:
                    {{
                        "en": "영어 번역",
                        "zh": "중국어 번역",
                        "zh_pron": "중국어 병음 (성조 포함)",
                        "zh_desc": "중국어 핵심 단어",
                        "ja": "일본어 번역",
                        "ja_pron": "일본어 전체 히라가나 발음",
                        "ja_desc": "일본어 중요 단어"
                    }}
                    """
                    
                    try:
                        # AI에게 편지 보내고 답장 받기
                        response = model.generate_content(prompt)
                        ai_data = json.loads(response.text) # AI가 준 답장을 딕셔너리로 변환
                        
                        results.append({
                            'ko': s, 
                            'en': ai_data.get('en', ''), 
                            'zh': ai_data.get('zh', ''), 
                            'zh_pron': ai_data.get('zh_pron', ''), 
                            'zh_desc': ai_data.get('zh_desc', ''),
                            'ja': ai_data.get('ja', ''), 
                            'ja_pron': ai_data.get('ja_pron', ''),
                            'ja_desc': ai_data.get('ja_desc', '')
                        })
                    except Exception as e:
                        st.error(f"AI 분석 중 오류 발생: {e}")
            
            st.session_state.scenario_data = results

    if st.session_state.scenario_data:
        st.divider()
        for i, data in enumerate(st.session_state.scenario_data):
            st.markdown(f"### {data['ko']}")
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.success("🇺🇸 영어")
                st.info(data['en'])
                if st.button("🔊 듣기", key=f"en_{i}"): speak(data['en'], 'en')
            with col2:
                st.success("🇨🇳 중국어")
                st.info(f"**{data['zh']}**\n\n*(병음: {data['zh_pron']})*")
                st.warning(f"**💡 문법 & 단어:**\n{data['zh_desc']}")
                if st.button("🔊 듣기", key=f"zh_{i}"): speak(data['zh'], 'zh-CN')
            with col3:
                st.success("🇯🇵 일본어")
                st.info(f"**{data['ja']}**\n\n*(발음: {data['ja_pron']})*")
                st.warning(f"**💡 문법 & 단어:**\n{data['ja_desc']}")
                if st.button("🔊 듣기", key=f"ja_{i}"): speak(data['ja'], 'ja')
            
            if st.button("💾 이 분석 결과 보관함에 저장", key=f"save_{i}"):
                conn = sqlite3.connect('my_sentences.db')
                c = conn.cursor()
                now = datetime.now().strftime("%Y-%m-%d %H:%M")
                c.execute("INSERT INTO sentences_v2 (date_added, ko, en, zh, zh_pron, zh_desc, ja, ja_pron, ja_desc, last_tested) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", 
                          (now, data['ko'], data['en'], data['zh'], data['zh_pron'], data['zh_desc'], data['ja'], data['ja_pron'], data['ja_desc'], '0000-00-00 00:00')) 
                conn.commit()
                conn.close()
                st.toast("✅ 저장 완료!")
            st.write("---")

# ==========================================
# [탭 2] 내 문장 보관함 (업데이트됨)
# ==========================================
with tab2:
    st.subheader("저장된 AI 분석 노트")
    conn = sqlite3.connect('my_sentences.db')
    c = conn.cursor()
    c.execute("SELECT * FROM sentences_v2 ORDER BY id DESC")
    records = c.fetchall()
    conn.close()

    if not records:
        st.info("저장된 문장이 없습니다.")
    else:
        for row in records:
            _, date_added, ko, en, zh, zh_pron, zh_desc, ja, ja_pron, ja_desc, last_tested = row
            with st.expander(f"📝 {ko}"):
                st.write(f"**🇺🇸 EN:** {en}")
                st.write(f"**🇨🇳 ZH:** {zh} ({zh_pron})")
                st.caption(f"💡 {zh_desc}")
                st.write(f"**🇯🇵 JA:** {ja} ({ja_pron})")
                st.caption(f"💡 {ja_desc}")
                st.write(f"*(저장일: {date_added})*")

# ==========================================
# [탭 3] 작문 테스트 (에빙하우스)
# ==========================================
with tab3:
    st.subheader("🎯 누적 작문 테스트 (오래된 순 5개)")
    
    if st.button("🔄 새로운 테스트 시작하기", type="primary"):
        conn = sqlite3.connect('my_sentences.db')
        c = conn.cursor()
        c.execute("SELECT * FROM sentences_v2 ORDER BY last_tested ASC LIMIT 5")
        st.session_state.test_sentences = c.fetchall()
        conn.close()

    if st.session_state.test_sentences:
        st.divider()
        with st.form("test_form"):
            for i, row in enumerate(st.session_state.test_sentences):
                idx, _, ko, en, zh, zh_pron, zh_desc, ja, ja_pron, ja_desc, _ = row
                st.markdown(f"**Q{i+1}. {ko}**")
                
                st.text_input("영어 작문:", key=f"ans_en_{i}")
                st.text_input("중국어/일본어 작문:", key=f"ans_other_{i}")
                
                with st.expander("👉 정답 확인하기"):
                    st.success(f"**EN:** {en}")
                    st.info(f"**ZH:** {zh} ({zh_pron})\n\n*(팁: {zh_desc})*")
                    st.warning(f"**JA:** {ja} ({ja_pron})\n\n*(팁: {ja_desc})*")
                st.write("---")
            
            submit_test = st.form_submit_button("✅ 테스트 완료 및 기록 업데이트")
            if submit_test:
                conn = sqlite3.connect('my_sentences.db')
                c = conn.cursor()
                now = datetime.now().strftime("%Y-%m-%d %H:%M")
                for row in st.session_state.test_sentences:
                    idx = row[0]
                    c.execute("UPDATE sentences_v2 SET last_tested = ? WHERE id = ?", (now, idx))
                conn.commit()
                conn.close()
                st.success("기록 저장 완료! 새로고침을 누르세요.")
                st.session_state.test_sentences = []