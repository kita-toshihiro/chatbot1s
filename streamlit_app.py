import streamlit as st
import sqlite3
import random
from pathlib import Path

# データベースの初期化
def init_db():
    conn = sqlite3.connect('toeic_quiz.db')
    c = conn.cursor()
    
    # テーブル作成
    c.execute('''
        CREATE TABLE IF NOT EXISTS words (
            id INTEGER PRIMARY KEY,
            word TEXT NOT NULL,
            meaning TEXT NOT NULL,
            level INTEGER DEFAULT 0
        )
    ''')
    
    c.execute('''
        CREATE TABLE IF NOT EXISTS quiz_results (
            id INTEGER PRIMARY KEY,
            word_id INTEGER,
            user_answer TEXT,
            correct_answer TEXT,
            is_correct INTEGER,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (word_id) REFERENCES words(id)
        )
    ''')
    
    # 初期単語データ（TOEIC 600点向けの単語）
    initial_words = [
        ('abandon', '放棄する', 1),
        ('ability', '能力', 1),
        ('able', '～できる', 1),
        ('about', '～について', 1),
        ('above', '～の上', 1),
        ('accept', '受け入れる', 1),
        ('access', 'アクセス', 1),
        ('accident', '事故', 1),
        ('across', '横切る', 1),
        ('act', '行動する', 1),
        ('action', '行動', 1),
        ('activity', '活動', 1),
        ('actually', '実際に', 1),
        ('add', '追加する', 1),
        ('address', '住所', 1),
        ('administration', '行政', 1),
        ('advantage', '利点', 1),
        ('advertisement', '広告', 1),
        ('advice', '助言', 1),
        ('advise', '勧める', 1),
        ('affect', '影響する', 1),
        ('afford', '～を買う/できる', 1),
        ('after', '～の後', 1),
        ('afternoon', '午後', 1),
        ('again', 'もう一度', 1),
        ('against', '～に反対して', 1),
        ('age', '年齢', 1),
        ('ago', '～前に', 1),
        ('agree', '同意する', 1),
        ('agreement', '合意', 1),
        ('air', '空気', 1),
        ('airplane', '飛行機', 1),
        ('airport', '空港', 1),
        ('alarm', '警報', 1),
        ('all', 'すべて', 1),
        ('allow', '許可する', 1),
        ('almost', 'ほとんど', 1),
        ('alone', '一人で', 1),
        ('along', '～に沿って', 1),
        ('already', 'もう', 1),
        ('also', 'また', 1),
        ('although', '～しかし', 1),
        ('always', '常に', 1),
        ('among', '～の間で', 1),
        ('amount', '量', 1),
        ('and', 'そして', 1),
        ('animal', '動物', 1),
        ('another', '別の', 1),
        ('answer', '答え', 1),
        ('any', 'いくつか', 1),
        ('anyone', 'だれでも', 1),
        ('anything', '何か', 1),
        ('anywhere', 'どこでも', 1),
        ('apartment', 'アパート', 1),
        ('appear', '現れる', 1),
        ('applaud', '拍手する', 1),
        ('application', 'アプリケーション', 1),
        ('appoint', '任命する', 1),
        ('approach', '接近する', 1),
        ('appropriate', '適切な', 1),
        ('approve', '承認する', 1),
        ('approximate', 'およそ', 1),
        ('area', '領域', 1),
        ('argue', '議論する', 1),
        ('argument', '議論', 1),
        ('arise', '発生する', 1),
        ('arrange', '手配する', 1),
        ('arrest', '逮捕する', 1),
        ('arrival', '到着', 1),
        ('arrive', '到着する', 1),
        ('art', '芸術', 1),
        ('article', '記事', 1),
        ('artist', '芸術家', 1),
        ('ash', '灰', 1),
        ('ashamed', '恥ずかしい', 1),
        ('ask', '尋ねる', 1),
        ('asleep', '眠っている', 1),
        ('associate', '関連させる', 1),
        ('assume', '仮定する', 1),
        ('astound', '驚かせる', 1),
        ('attach', '付ける', 1),
        ('attack', '攻撃する', 1),
        ('attempt', '試みる', 1),
        ('attend', '出席する', 1),
        ('attitude', '態度', 1),
        ('attract', '魅力的にする', 1),
        ('audience', '聴衆', 1),
        ('authority', '権威', 1),
        ('automatic', '自動的な', 1),
        ('available', '利用可能な', 1),
    ]
    
    for word in initial_words:
        c.execute('INSERT INTO words (word, meaning, level) VALUES (?, ?, ?)', word)
    
    conn.commit()
    conn.close()

# データベース接続関数
def get_db_connection():
    conn = sqlite3.connect('toeic_quiz.db')
    conn.row_factory = sqlite3.Row
    return conn

# 4択問題を作成する関数
def create_quiz_option(correct_answer):
    other_words = get_all_words()
    options = [correct_answer]
    
    while len(options) < 4:
        random_word = random.choice(other_words)
        if random_word['word'] != correct_answer['word'] and random_word['word'] not in 
options:
            options.append(random_word['word'])
    
    random.shuffle(options)
    return options

# すべての単語を取得する関数
def get_all_words():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM words')
    words = cursor.fetchall()
    conn.close()
    return words

# 間違えた単語を取得する関数
def get_wrong_words():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT DISTINCT w.* FROM words w
        JOIN quiz_results q ON w.id = q.word_id
        WHERE q.is_correct = 0
    ''')
    wrong_words = cursor.fetchall()
    conn.close()
    return wrong_words

# クイズを開始する関数
def start_quiz():
    st.session_state.quiz_mode = 'normal'
    st.session_state.current_question = 0
    st.session_state.score = 0
    st.session_state.wrong_answers = []
    
    # メインクイズ画面へ遷移
    st.session_state.page = 'main_quiz'

# 復習モードを開始する関数
def start_review_mode():
    st.session_state.quiz_mode = 'review'
    st.session_state.current_question = 0
    st.session_state.score = 0
    st.session_state.wrong_answers = []
    
    # 復習モード画面へ遷移
    st.session_state.page = 'review_quiz'

# クイズを終了する関数
def end_quiz():
    st.session_state.page = 'result'

# Streamlitアプリの構築
def main():
    # セッションステートの初期化
    if 'page' not in st.session_state:
        st.session_state.page = 'home'
    if 'quiz_mode' not in st.session_state:
        st.session_state.quiz_mode = 'normal'
    if 'score' not in st.session_state:
        st.session_state.score = 0
    if 'current_question' not in st.session_state:
        st.session_state.current_question = 0
    if 'wrong_answers' not in st.session_state:
        st.session_state.wrong_answers = []
    
    # データベースの初期化
    init_db()
    
    # ページ遷移に応じた表示
    if st.session_state.page == 'home':
        show_home_page()
    elif st.session_state.page == 'main_quiz':
        show_main_quiz()
    elif st.session_state.page == 'review_quiz':
        show_review_quiz()
    elif st.session_state.page == 'result':
        show_result_page()
    elif st.session_state.page == 'wrong_words':
        show_wrong_words_page()

# ホームページの表示
def show_home_page():
    st.title("TOEIC 600点合格 英単語クイズ")
    st.header("ホーム")
    st.markdown("""
    このアプリはTOEIC 600点合格を目指した英単語学習用です。
    
    ### メイン機能：
    - 200語の英単語クイズ
    - 解答履歴の保存
    - 間違えた単語の復習
    - 成績の表示
    
    ### スタート画面
    """)
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("メインクイズを開始"):
            start_quiz()
    with col2:
        if st.button("復習モードを開始"):
            wrong_words = get_wrong_words()
            if wrong_words:
                start_review_mode()
            else:
                st.warning("まだ間違えた単語はありません")

# メインクイズ画面の表示
def show_main_quiz():
    words = get_all_words()
    random.shuffle(words)
    
    if st.session_state.current_question < len(words):
        current_word = words[st.session_state.current_question]
        options = create_quiz_option(current_word)
        
        st.header(f"問題 {st.session_state.current_question + 1} / {len(words)}")
        st.subheader(f"英単語: {current_word['word']}")
        
        user_answer = st.radio("意味を選択してください:", options)
        
        if st.button("回答する"):
            if user_answer == current_word['meaning']:
                st.success("正解です！")
                st.session_state.score += 1
                # 正解記録を保存
                save_result(current_word['id'], user_answer, current_word['meaning'], 1)
            else:
                st.error(f"不正解です。正解は: {current_word['meaning']}")
                st.session_state.wrong_answers.append(current_word['word'])
                # 不正解記録を保存
                save_result(current_word['id'], user_answer, current_word['meaning'], 0)
            
            st.session_state.current_question += 1
            st.rerun()
    else:
        st.success("クイズ終了！")
        st.write(f"得点: {st.session_state.score} / {len(words)}")
        st.write(f"正解率: {st.session_state.score / len(words) * 100:.1f}%")
        
        if st.button("結果ページへ戻る"):
            st.session_state.page = 'result'

# 復習モードの表示
def show_review_quiz():
    wrong_words = get_wrong_words()
    
    if st.session_state.current_question < len(wrong_words):
        current_word = wrong_words[st.session_state.current_question]
        options = create_quiz_option(current_word)
        
        st.header(f"復習問題 {st.session_state.current_question + 1} / 
{len(wrong_words)}")
        st.subheader(f"英単語: {current_word['word']}")
        
        user_answer = st.radio("意味を選択してください:", options)
        
        if st.button("回答する"):
            if user_answer == current_word['meaning']:
                st.success("正解です！")
                st.session_state.score += 1
            else:
                st.error(f"不正解です。正解は: {current_word['meaning']}")
                st.session_state.wrong_answers.append(current_word['word'])
            
            st.session_state.current_question += 1
            st.rerun()
    else:
        st.success("復習終了！")
        st.write(f"正解数: {st.session_state.score} / {len(wrong_words)}")
        st.write(f"正解率: {st.session_state.score / len(wrong_words) * 100:.1f}%")
        
        if st.button("結果ページへ戻る"):
            st.session_state.page = 'result'

# 結果ページの表示
def show_result_page():
    total_words = get_all_words()
    score = st.session_state.score
    total = len(total_words)
    
    st.title("クイズ結果")
    st.header("結果発表")
    
    st.write(f"クイズ回数: {total}")
    st.write(f"正解数: {score}")
    st.write(f"不正解数: {total - score}")
    st.write(f"正解率: {score / total * 100:.1f}%")
    
    wrong_words = get_wrong_words()
    if wrong_words:
        st.header("間違えた単語リスト")
        for word in wrong_words:
            st.write(f"- {word['word']}: {word['meaning']}")
    else:
        st.success("すごい！すべて正解しました！")
    
    st.button("ホームに戻る", on_click=lambda: st.session_state.update(page='home'))

# 間違えた単語ページの表示
def show_wrong_words_page():
    wrong_words = get_wrong_words()
    
    st.title("間違えた単語リスト")
    st.header("学習用リスト")
    
    for word in wrong_words:
        st.write(f"- {word['word']}: {word['meaning']}")
    
    st.button("ホームに戻る", on_click=lambda: st.session_state.update(page='home'))

# 結果を保存する関数
def save_result(word_id, user_answer, correct_answer, is_correct):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO quiz_results (word_id, user_answer, correct_answer, is_correct)
        VALUES (?, ?, ?, ?)
    ''', (word_id, user_answer, correct_answer, is_correct))
    conn.commit()
    conn.close()

# アプリケーションの実行
if __name__ == "__main__":
    main()
