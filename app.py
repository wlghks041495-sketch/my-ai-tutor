import streamlit as st
from deep_translator import GoogleTranslator, DeeplTranslator
from gtts import gTTS
import os
import base64
import sqlite3
import re
from datetime import datetime
import jieba
from pypinyin import pinyin, Style
import pykakasi

# 1. 화면 설정
st.set_page_config(page_title="무제한 로컬 어학기", layout="wide")

# 2. 딥엘 키 가져오기
DEEPL_KEY = st.secrets.get("DEEPL_API_KEY", "")

# 3. 데이터베이스 세팅 (기존과 동일)
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

# 4. 음성 재생 함수
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

# 5. 로컬 분석 함수
def analyze_chinese(text):
    words = jieba.lcut(text)
    unique_words = [w for w in words if len(w) > 1]
    desc = "추출 단어: " + ", ".join(unique_words)
    pron = " ".join([p[0] for p in pinyin(text, style=Style.TONE)])
    return pron, desc

def analyze_japanese(text):
    kks = pykakasi.kakasi()
    result = kks.convert(text)
    pron = " ".join([item['hira'] for item in result])
    unique_words = [item['orig'] for item in result if item['orig'] != item['hira']]
    desc = "추출 단어(한자): " + ", ".join(list(set(unique_words)))
    return pron, desc

# 🌟 6. [핵심] 번역기 출처와 에러 원인을 반환하는 스마트 번역기
def smart_translate(text, target_lang):
    deepl_lang = 'en-US' if target_lang == 'en' else target_lang
    google_lang = 'zh-CN' if target_lang == 'zh' else target_lang
    
    error_msg = ""

    # [1순위] DeepL 시도
    if DEEPL_KEY:
        try:
            # 번역 성공 시 결과와 함께 'DeepL' 태그 반환
            result = DeeplTranslator(api_key=DEEPL_KEY, source="auto", target=deepl_lang, use_free_api=True).translate(text)
            return result, "DeepL", "" 
        except Exception as e: 
            error_msg = str(e) # 딥엘 실패 원인을 저장해둠

    # [2순위] Google (DeepL이 실패했거나 키가 없을 때)
    try:
        result = GoogleTranslator(source='ko', target=google_lang).translate(text)
        return result, "Google", error_msg # 구글 번역 결과와 함께 딥엘의 에러 원인도 같이 보냄
    except:
        return "[번역 실패] 잠시 후 다시 시도해주세요.", "Error", ""

# 세션 세팅
if 'scenario_data' not in st.session_state:
    st.session_state.scenario_data = []
if 'test_sentences' not in st.session_state:
    st.session_state.test_sentences = []

st.title("🚀 무제한 로컬 어학 학습기")
st.caption("결과 창에서 DeepL / Google 출처를 직접 확인하세요!")

tab1, tab2, tab3 = st.tabs(["📝 오늘의 학습", "📚 내 보관함", "🎯 작문 테스트"])

# ==========================================
# [탭 1] 오늘의 학습
# ==========================================
with tab1:
    input_text = st.text_area("공부할 한국어 문장을 입력하세요:", height=100)

    if st.button("분석 시작", type="primary"):
        if input_text:
            raw_sentences = re.split(r'(?<=[.!?])\s+|\n+', input_text)
            sentences = [s.strip() for s in raw_sentences if s.strip()]
            
            results = []
            with st.spinner("최적의 번역기를 찾아 분석 중입니다..."):
                for s in sentences:
                    if len(s) < 2: continue
                        
                    # 번역 결과, 사용된 엔진, 에러 원인(있을 경우)을 모두 받아옴
                    en, en_engine, en_err = smart_translate(s, 'en')
                    zh, zh_engine, zh_err = smart_translate(s, 'zh')
                    ja, ja_engine, ja_err = smart_translate(s, 'ja')
                    
                    zh_pron, zh_desc = analyze_chinese(zh)
                    ja_pron, ja_desc = analyze_japanese(ja)
                    
                    results.append({
                        'ko': s, 
                        'en': en, 'en_engine': en_engine, 'en_err': en_err,
                        'zh': zh, 'zh_engine': zh_engine, 'zh_err': zh_err, 'zh_pron': zh_pron, 'zh_desc': zh_desc,
                        'ja': ja, 'ja_engine': ja_engine, 'ja_err': ja_err, 'ja_pron': ja_pron, 'ja_desc': ja_desc
                    })
            st.session_state.scenario_data = results

    if st.session_state.scenario_data:
        for i, data in enumerate(st.session_state.scenario_data):
            st.markdown(f"### {data['ko']}")
            col1, col2, col3 = st.columns(3)
            with col1:
                # 🌟 화면에 [DeepL] 또는 [Google] 태그 표시
                st.success(f"🇺🇸 영어 [{data['en_engine']}]")
                st.info(data['en'])
                if data['en_err']: st.error(f"DeepL 실패 원인: {data['en_err']}")
                if st.button("🔊", key=f"en_{i}"): speak(data['en'], 'en')
            with col2:
                st.success(f"🇨🇳 중국어 [{data['zh_engine']}]")
                st.info(f"{data['zh']}\n\n({data['zh_pron']})")
                if data['zh_err']: st.error(f"DeepL 실패 원인: {data['zh_err']}")
                st.caption(data['zh_desc'])
                if st.button("🔊", key=f"zh_{i}"): speak(data['zh'], 'zh-CN')
            with col3:
                st.success(f"🇯🇵 일본어 [{data['ja_engine']}]")
                st.info(f"{data['ja']}\n\n({data['ja_pron']})")
                if data['ja_err']: st.error(f"DeepL 실패 원인: {data['ja_err']}")
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
# [탭 2] 내 보관함 / [탭 3] 작문 테스트는 기존과 동일하게 유지
# ==========================================
with tab2:
    st.subheader("저장된 분석 노트")
    conn = sqlite3.connect('my_sentences_local.db')
    c = conn.cursor()
    c.execute("SELECT * FROM sentences_local ORDER BY id DESC")
    records = c.fetchall()
    conn.close()

    if not records:
        st.info("저장된 문장이 없습니다.")
    else:
        for row in records:
            idx, date_added, ko, en, zh, zh_pron, zh_desc, ja, ja_pron, ja_desc, last_tested = row
            with st.expander(f"📝 {ko}"):
                st.write(f"**🇺🇸 EN:** {en}")
                st.write(f"**🇨🇳 ZH:** {zh} ({zh_pron})")
                st.caption(f"💡 {zh_desc}")
                st.write(f"**🇯🇵 JA:** {ja} ({ja_pron})")
                st.caption(f"💡 {ja_desc}")
                st.write(f"*(저장일: {date_added})*")
                
                if st.button("🗑️ 삭제하기", key=f"del_{idx}"):
                    conn = sqlite3.connect('my_sentences_local.db')
                    c = conn.cursor()
                    c.execute("DELETE FROM sentences_local WHERE id = ?", (idx,))
                    conn.commit()
                    conn.close()
                    st.rerun()

with tab3:
    st.subheader("🎯 누적 작문 테스트")
    if st.button("🔄 새로운 테스트 시작하기", type="primary"):
        conn = sqlite3.connect('my_sentences_local.db')
        c = conn.cursor()
        c.execute("SELECT * FROM sentences_local ORDER BY last_tested ASC LIMIT 5")
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
                conn = sqlite3.connect('my_sentences_local.db')
                c = conn.cursor()
                now = datetime.now().strftime("%Y-%m-%d %H:%M")
                for row in st.session_state.test_sentences:
                    idx = row[0]
                    c.execute("UPDATE sentences_local SET last_tested = ? WHERE id = ?", (now, idx))
                conn.commit()
                conn.close()
                st.success("기록 완료! 새 테스트를 눌러주세요.")
                st.session_state.test_sentences = []
