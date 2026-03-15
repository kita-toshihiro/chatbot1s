import streamlit as st
import pandas as pd
import random

# --- データ読み込み ---
try:
    df = pd.read_csv("data.csv")
except FileNotFoundError:
    st.error("data.csv が見つかりません。ファイルが存在することを確認してく
ださい。")
    st.stop()

# --- セッションステートの初期化 ---
if 'answered' not in st.session_state:
    st.session_state.answered = []  # 解答履歴
if 'wrong_words' not in st.session_state:
    st.session_state.wrong_words = [] # 間違えた単語
if 'word_index' not in st.session_state:
    st.session_state.word_index = [] # 出題済みの単語index

# --- 関数定義 ---

def get_random_word(df, word_index):
    """ランダムに単語を選び、出題済みの単語を除外する"""
    available_indices = [i for i in range(len(df)) if i not in word_index]
    if not available_indices:
        st.warning("全ての単語が出題されました。")
        return None, None, None

    random_index = random.choice(available_indices)
    word = df.iloc[random_index]['英単語']
    meaning = df.iloc[random_index]['意味']
    return word, meaning, random_index

def check_answer(user_answer, correct_meaning, word, word_index, answered, 
wrong_words):
    """解答をチェックし、解答履歴と間違え単語リストを更新する"""
    if user_answer.strip().lower() == correct_meaning.strip().lower():
        st.success("正解！")
        answered.append((word, "正解"))
    else:
        st.error(f"不正解。正解は: {correct_meaning}")
        answered.append((word, "不正解"))
        wrong_words.append(word)
    
    return answered, wrong_words

# --- メインアプリケーション ---

st.title("TOEIC 600点対策 英単語クイズ")

mode = st.sidebar.radio("モードを選択:", ("クイズ", "復習"))

if mode == "クイズ":
    st.header("クイズモード")

    if st.button("次の問題"):
        word, meaning, random_index = get_random_word(df, 
st.session_state.word_index)

        if word is None:
            st.stop()

        st.session_state.word_index.append(random_index)

        st.write(f"**問題:** {word}")
        user_answer = st.text_input("意味を入力してください:")

        if st.button("解答"):
            st.session_state.answered, st.session_state.wrong_words = 
check_answer(user_answer, meaning, word, st.session_state.word_index, 
st.session_state.answered, st.session_state.wrong_words)

    # 解答履歴の表示
    st.subheader("解答履歴")
    if st.session_state.answered:
        for word, result in st.session_state.answered:
            st.write(f"{word}: {result}")
    else:
        st.write("まだ解答していません。")

elif mode == "復習":
    st.header("復習モード")

    if not st.session_state.wrong_words:
        st.write("間違えた単語はありません。")
    else:
        # 間違えた単語のみを出題
        wrong_words = st.session_state.wrong_words
        random.shuffle(wrong_words) # 毎回順番を変える
        
        for word in wrong_words:
            meaning = df[df['英単語'] == word]['意味'].values[0]
            st.write(f"**問題:** {word}")
            user_answer = st.text_input("意味を入力してください:")
            if st.button("解答"):
                if user_answer.strip().lower() == meaning.strip().lower():
                    st.success("正解！")
                    st.session_state.wrong_words.remove(word)
                else:
                    st.error(f"不正解。正解は: {meaning}")
