import streamlit as st
import pandas as pd
import sqlite3
import random

# DB接続
def init_db():
    conn = sqlite3.connect('quiz.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS quiz_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            word TEXT,
            correct BOOLEAN,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

# 単語データ読み込み
@st.cache_data
def load_words():
    df = pd.read_csv('words.csv')
    return df

# 単語の選択
def get_random_word(words_df):
    return words_df.sample(1).iloc[0]

# 解答履歴の保存
def save_answer(word, is_correct):
    conn = sqlite3.connect('quiz.db')
    c = conn.cursor()
    c.execute("INSERT INTO quiz_history (word, correct) VALUES (?, ?)", 
(word, is_correct))
    conn.commit()
    conn.close()

# 間違えた単語の取得
def get_mistakes():
    conn = sqlite3.connect('quiz.db')
    df = pd.read_sql_query("SELECT DISTINCT word FROM quiz_history WHERE 
correct = 0", conn)
    conn.close()
    return df['word'].tolist()

# クイズ表示
def quiz_app():
    st.title("TOEIC 600点を目指す英単語クイズ")
    words_df = load_words()
    history = get_mistakes()

    # モード選択
    mode = st.radio("モードを選択", ["通常モード", "復習モード"])

    if mode == "復習モード":
        if not history:
            st.write("復習する単語がありません。")
            return
        words_to_review = words_df[words_df['English'].isin(history)]
        word = get_random_word(words_to_review)
    else:
        word = get_random_word(words_df)

    st.write(f"単語: **{word['English']}**")
    answer = st.text_input("日本語訳を入力してください")

    if st.button("解答"):
        if answer.strip() == word['Japanese']:
            st.success("正解!")
            save_answer(word['English'], True)
        else:
            st.error(f"不正解。正解は: {word['Japanese']}")
            save_answer(word['English'], False)

    # 間違えた単語一覧表示
    if st.button("間違えた単語を表示"):
        mistakes = get_mistakes()
        if mistakes:
            st.write("間違えた単語:")
            for word in mistakes:
                st.write(f"- {word}")
        else:
            st.write("間違えた単語はありません。")

# メイン
if __name__ == "__main__":
    init_db()
    quiz_app()
