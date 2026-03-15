import streamlit as st
import random
import pandas as pd

# --- データ準備 (TOEIC 600点レベルのサンプル単語) ---
# 本来は200語用意しますが、ここではサンプルとして一部を掲載します。
# 実際にはこのリストを200語まで拡張してください。
WORDS_DATA = [
    {"word": "submit", "meaning": "を提出する", "example": "Please submit the report by Friday."},
    {"word": "identify", "meaning": "を特定する", "example": "We need to identify the cause of the problem."},
    {"word": "opportunity", "meaning": "機会", "example": "It's a great opportunity to learn."},
    {"word": "confirm", "meaning": "を確認する", "example": "I'd like to confirm my reservation."},
    {"word": "provide", "meaning": "を提供する", "example": "The company provides medical insurance."},
    {"word": "benefit", "meaning": "利益、特典", "example": "One of the benefits of this job is flexible hours."},
    {"word": "purchase", "meaning": "を購入する", "example": "You can purchase tickets online."},
    {"word": "announce", "meaning": "を発表する", "example": "The CEO announced a new plan."},
    {"word": "representative", "meaning": "担当者、代表者", "example": "Please speak with a customer service representative."},
    {"word": "require", "meaning": "を必要とする", "example": "The job requires several years of experience."},
    # ここに200語まで追加...
]

# --- セッション状態の初期化 ---
if 'history' not in st.session_state:
    st.session_state.history = []  # 全解答ログ
if 'wrong_words' not in st.session_state:
    st.session_state.wrong_words = set()  # 間違えた単語のセット
if 'current_question' not in st.session_state:
    st.session_state.current_question = None

def get_new_question(mode="通常"):
    if mode == "復習" and st.session_state.wrong_words:
        # 間違えた単語から選ぶ
        target_word = random.choice([w for w in WORDS_DATA if w['word'] in st.session_state.wrong_words])
    else:
        target_word = random.choice(WORDS_DATA)
    
    # 選択肢の作成（正解1つ + 不正解3つ）
    distractors = random.sample([w['meaning'] for w in WORDS_DATA if w['meaning'] != target_word['meaning']], k=3)
    options = distractors + [target_word['meaning']]
    random.shuffle(options)
    
    return {
        "word": target_word['word'],
        "correct": target_word['meaning'],
        "options": options,
        "example": target_word['example']
    }

# --- UI レイアウト ---
st.title("🚀 TOEIC 600点突破！英単語クイズ")

# サイドバー：モード選択と進捗
st.sidebar.header("メニュー")
mode = st.sidebar.radio("モード選択", ["通常学習", "復習モード (誤答のみ)"])

if st.sidebar.button("次の問題へ"):
    st.session_state.current_question = get_new_question("復習" if "復習" in mode else "通常")
    st.rerun()

# --- メインコンテンツ ---
if st.session_state.current_question is None:
    st.info("「次の問題へ」ボタンを押してクイズを開始してください。")
else:
    q = st.session_state.current_question
    st.subheader(f"単語: **{q['word']}**")
    
    with st.form(key='quiz_form'):
        answer = st.radio("正しい意味を選んでください:", q['options'])
        submit_button = st.form_submit_button(label='回答する')

    if submit_button:
        is_correct = (answer == q['correct'])
        
        if is_correct:
            st.success("正解です！")
            # 復習モードで正解したらリストから消す処理（任意）
            if q['word'] in st.session_state.wrong_words:
                st.session_state.wrong_words.remove(q['word'])
        else:
            st.error(f"不正解... 正解は 「{q['correct']}」 です。")
            st.session_state.wrong_words.add(q['word'])
            st.write(f"例文: {q['example']}")

        # 履歴に保存
        st.session_state.history.append({
            "単語": q['word'],
            "あなたの回答": answer,
            "正解": q['correct'],
            "判定": "○" if is_correct else "×"
        })

# --- データ表示エリア ---
st.divider()
col1, col2 = st.columns(2)

with col1:
    st.subheader("📊 今回の学習記録")
    if st.session_state.history:
        df_history = pd.DataFrame(st.session_state.history)
        st.dataframe(df_history.iloc[::-1], use_container_width=True) # 新しい順に表示

with col2:
    st.subheader("⚠️ 復習が必要な単語")
    if st.session_state.wrong_words:
        st.write(list(st.session_state.wrong_words))
        if st.button("復習リストをリセット"):
            st.session_state.wrong_words = set()
            st.rerun()
    else:
        st.write("現在、間違えた単語はありません！")
