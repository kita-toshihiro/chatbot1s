import streamlit as st
import random
import json
import sqlite3
import datetime
import os
from pathlib import Path

# --------------------------------------------------
# 1. データベース接続 & 初期化
# --------------------------------------------------
DB_PATH = Path("quiz.db")      # ローカル開発用。Cloud では外部 DB に置き換えてください。


def get_conn():
    conn = sqlite3.connect(str(DB_PATH))
    return conn

def init_db():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS attempts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            word TEXT NOT NULL,
            user_answer TEXT NOT NULL,
            is_correct INTEGER NOT NULL,
            ts TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()

# --------------------------------------------------
# 2. 単語リスト読み込み
# --------------------------------------------------
def load_words():
    # words.json は {"word": "example", "meaning": "…"} 形式
    with open("words.json", encoding="utf-8") as f:
        words = json.load(f)
    return words

# --------------------------------------------------
# 3. DB 操作
# --------------------------------------------------
def record_attempt(word, answer, is_correct):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO attempts (word, user_answer, is_correct, ts)
        VALUES (?, ?, ?, ?)
    """, (word, answer, int(is_correct), datetime.datetime.now().isoformat()))
    conn.commit()
    conn.close()

def get_wrong_words():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT DISTINCT word FROM attempts WHERE is_correct = 0")
    rows = cur.fetchall()
    conn.close()
    return [row[0] for row in rows]

def get_attempts_by_word(word):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT user_answer, is_correct, ts FROM attempts WHERE word = ?", 
(word,))
    rows = cur.fetchall()
    conn.close()
    return rows

# --------------------------------------------------
# 4. Streamlit UI
# --------------------------------------------------
st.set_page_config(page_title="TOEIC 600 語彙クイズ", layout="centered")

# データベース初期化
init_db()

# サイドバーでモード選択
mode = st.sidebar.radio("モード", ["クイズ", "復習", "結果リスト"])

# 単語リスト取得
ALL_WORDS = load_words()
WORD_DICT = {w["word"]: w for w in ALL_WORDS}

# --------------------------------------------------
# 5. クイズモード
# --------------------------------------------------
if mode == "クイズ":
    if "quiz_index" not in st.session_state:
        st.session_state.quiz_index = 0
    if "quiz_words" not in st.session_state:
        # ランダムにシャッフル
        st.session_state.quiz_words = random.sample(list(WORD_DICT.keys()), 
len(WORD_DICT))

    current_word = st.session_state.quiz_words[st.session_state.quiz_index]
    meaning = WORD_DICT[current_word]["meaning"]

    st.title(f"単語：{current_word}")
    st.write("**意味は？**")

    user_answer = st.text_input("答えを入力", key="user_answer")

    if st.button("確認"):
        is_correct = (user_answer.strip().lower() == meaning.lower())
        if is_correct:
            st.success("正解！ 🎉")
        else:
            st.error(f"不正解... 正しい意味は：{meaning}")

        # DBに保存
        record_attempt(current_word, user_answer, is_correct)

        # 次へ
        st.session_state.quiz_index += 1
        if st.session_state.quiz_index >= len(st.session_state.quiz_words):
            st.session_state.quiz_index = 0
            st.success("全単語をクイズしました！ 次からは再スタートします。")

# --------------------------------------------------
# 6. 復習モード
# --------------------------------------------------
elif mode == "復習":
    wrong_words = get_wrong_words()
    if not wrong_words:
        st.info("間違えた単語はありません！ 🎉")
    else:
        if "review_index" not in st.session_state:
            st.session_state.review_index = 0
        if "review_words" not in st.session_state:
            st.session_state.review_words = random.sample(wrong_words, len(wrong_words))

        current_word = st.session_state.review_words[st.session_state.review_index]
        meaning = WORD_DICT[current_word]["meaning"]

        st.title(f"復習 - 単語：{current_word}")
        st.write("**意味は？**")

        user_answer = st.text_input("答えを入力", key="review_answer")

        if st.button("確認"):
            is_correct = (user_answer.strip().lower() == meaning.lower())
            if is_correct:
                st.success("正解！ 🎉")
                # 正解の場合は DB から除外しても良い
                record_attempt(current_word, user_answer, True)
            else:
                st.error(f"不正解... 正しい意味は：{meaning}")
                record_attempt(current_word, user_answer, False)

            st.session_state.review_index += 1
            if st.session_state.review_index >= len(st.session_state.review_words):
                st.session_state.review_index = 0
                st.success("復習完了！")

# --------------------------------------------------
# 7. 結果リスト
# --------------------------------------------------
elif mode == "結果リスト":
    word = st.selectbox("単語を選択", list(WORD_DICT.keys()))
    attempts = get_attempts_by_word(word)
    if not attempts:
        st.info("まだ解答がありません。")
    else:
        df = pd.DataFrame(attempts, columns=["自分の回答", "正誤", "日時"])
        df["正誤"] = df["正誤"].map({1: "正解", 0: "不正解"})
        st.table(df)
