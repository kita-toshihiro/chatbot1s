import streamlit as st
import pandas as pd
import random
import csv
import os
from datetime import datetime

# -----------------------------
# ① データ読み込み（キャッシュ）
# -----------------------------
@st.cache_data(show_spinner=False)
def load_words(csv_path="words.csv"):
    return pd.read_csv(csv_path)

@st.cache_data(show_spinner=False)
def load_answers(csv_path="answers.csv"):
    if not os.path.exists(csv_path):
        # ファイルが無ければヘッダーだけ作成
        with open(csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["timestamp","word","meaning","answer","correct"])
    return pd.read_csv(csv_path)

# -----------------------------
# ② 保存処理
# -----------------------------
def append_answer(timestamp, word, meaning, answer, correct):
    # 追記モードで書き込む
    with open("answers.csv", "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([timestamp, word, meaning, answer, correct])

# -----------------------------
# ③ 間違いリスト取得
# -----------------------------
def get_wrong_entries(df):
    return df[df["correct"] == False]

# -----------------------------
# ④ UI
# -----------------------------
st.set_page_config(page_title="TOEIC 600点単語クイズ", layout="wide")

st.title("📚 TOEIC 600点単語クイズ")

# ① Sidebar: モード選択
mode = st.sidebar.radio(
    "モードを選択してください",
    ("Quiz", "Review", "Results")
)

words_df = load_words()
answers_df = load_answers()

# -----------------------------
# 本試験モード（Quiz）
# -----------------------------
if mode == "Quiz":
    st.subheader("💡 単語を覚えよう！")
    
    # ランダムに単語を選択
    if "current_word" not in st.session_state:
        st.session_state.current_word = random.choice(words_df.to_dict('records'))
    
    cur = st.session_state.current_word
    st.write(f"**単語:** {cur['word']}")
    st.write(f"**意味（ヒント）:** {cur['meaning'][:3]}...")  # 最初の3文字だけ表示
    
    user_ans = st.text_input("英訳は？", key="user_ans")
    
    if st.button("送信"):
        correct = user_ans.strip().lower() == cur['meaning'].strip().lower()
        append_answer(
            timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            word=cur['word'],
            meaning=cur['meaning'],
            answer=user_ans,
            correct=correct
        )
        if correct:
            st.success("✅ 正解！")
        else:
            st.error(f"❌ 誤り。正しい答えは「{cur['meaning']}」です。")
        # 次の単語に移行
        st.session_state.current_word = random.choice(words_df.to_dict('records'))
        st.experimental_rerun()  # 状態更新を確実に

# -----------------------------
# 復習モード（Review）
# -----------------------------
elif mode == "Review":
    st.subheader("🔁 復習モード")
    
    wrong_df = get_wrong_entries(answers_df)
    
    if wrong_df.empty:
        st.info("間違いはありません！ 🎉")
    else:
        # ランダムに1語を選ぶ
        cur = wrong_df.sample(n=1).iloc[0]
        st.write(f"**単語:** {cur['word']}")
        st.write(f"**意味（ヒント）:** {cur['meaning'][:3]}...")
        user_ans = st.text_input("英訳は？", key="review_ans")
        
        if st.button("送信"):
            correct = user_ans.strip().lower() == cur['meaning'].strip().lower()
            append_answer(
                timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                word=cur['word'],
                meaning=cur['meaning'],
                answer=user_ans,
                correct=correct
            )
            if correct:
                st.success("✅ 正解！")
            else:
                st.error(f"❌ 誤り。正しい答えは「{cur['meaning']}」です。")
            st.experimental_rerun()

# -----------------------------
# 結果表示モード（Results）
# -----------------------------
elif mode == "Results":
    st.subheader("📊 これまでの回答履歴")
    # 再度読み直して最新データを取得
    answers_df = load_answers()
    st.dataframe(answers_df.style.set_properties(**{'text-align':'left'}))
    
    # 間違いリストをリセット
    if st.button("Reset Wrong List"):
        # すべて正解に書き換え
        answers_df.loc[answers_df["correct"] == False, "correct"] = True
        answers_df.to_csv("answers.csv", index=False)
        st.success("間違いリストをクリアしました。")
        st.experimental_rerun()
