import streamlit as st
import sqlite3
import pandas as pd
import os
import datetime
from pathlib import Path

# ============================
# ⚙️ 設定と関数定義
# ============================

DB_NAME = "study.db"  # データベースファイル名（同一ディレクトリ内）
WORD_CSV_PATH = "words.csv"
SESSION_LIMIT = 5  # セッションあたりの出題制限数（0=無限）
SESSION_KEY = 'word_session_state'

def get_db_connection():
    """DB 接続を取得"""
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """データベース初期化（安全に）"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # 作成テーブルの存在チェックと自動生成（IF NOT EXISTS）
        cursor.execute(f'''
            CREATE TABLE IF NOT EXISTS word_stats (
                id INTEGER PRIMARY KEY,
                word_text TEXT NOT NULL,
                total_attempts INTEGER DEFAULT 0,
                correct_attempts INTEGER DEFAULT 0
            )
        ''')

        cursor.execute(f'''
            CREATE TABLE IF NOT EXISTS quiz_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                word_id INTEGER,
                word_text TEXT,
                translation_text TEXT,
                user_answer TEXT,
                correct_answer TEXT,
                is_correct INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (word_id) REFERENCES word_stats(id)
            )
        ''')
        
        conn.commit()
    except sqlite3.Error as e:
        st.error(f"⚠️ データベース作成エラー：{e}")
    finally:
        conn.close()

def load_words_from_csv():
    """CSV から単語データをロード（既存の DB に統合）"""
    if not os.path.exists(WORD_CSV_PATH):
        return []
    
    df = pd.read_csv(WORD_CSV_PATH, encoding="utf-8")
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    for index, row in df.iterrows():
        word_id = row['id'] if 'id' in row.index else (index + 1)  # ID の優先順位を確保
        
        # テーブル存在チェック（エラー対策）
        try:
            cursor.execute(f'''
                SELECT total_attempts, correct_attempts 
                FROM word_stats WHERE id = {word_id}
            ''')
            res = cursor.fetchone()
            
            if res is None:
                cursor.execute(f'''
                    INSERT OR IGNORE INTO word_stats (id, word_text, total_attempts, correct_attempts)
                    VALUES ({word_id}, "{row['word']}", 0, {int(row.get('correct', 0))})
                ''')
        
        except sqlite3.OperationalError as e:
            # コラム名不一致などの場合、スキップして警告
            st.warning(f"⚠️ {word_id} 番目の単語の DB 登録が失敗しました：{e}")
    
    conn.commit()
    return len(df)

def get_stats():
    """学習統計を取得"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 正答率計算
    cursor.execute(f'''
        SELECT 
            COUNT(*) as total,
            SUM(correct_attempts) as correct,
            CASE WHEN COUNT(*) > 0 THEN ROUND(SUM(correct_attempts)*1.0/COUNT(*),2) ELSE 0 END as accuracy_rate
        FROM word_stats
    ''')
    
    result = cursor.fetchone()
    conn.close()
    return {
        'total_words': result['total'],
        'correct_words': int(result['correct']),
        'accuracy': float(result['accuracy_rate'])
    }

# ============================
# 📄 メインアプリロジック
# ============================

@st.cache_resource  # DB はセッション間でも共有（Streamlit Cloud で重要）
def main_app():
    st.set_page_config(page_title="TOEIC 単語学習アプリ", layout="wide")
    
    # セッションステート管理
    if 'history_count' not in st.session_state:
        st.session_state.history_count = 0
    
    # データベース初期化（各セッションで実行しないよう、必要ならデプロイ時に一度だけ）
    try:
        conn = get_db_connection()
        # テーブル作成は初回のみ（既存 DB と競合を防ぐ）
        init_db()
        conn.close()
    except Exception as e:
        st.error(f"❌ データベース初期化エラー：{e}")
    
    # 統計取得と表示
    stats = get_stats()
    col1, col2, col3 = st.columns([0.6, 0.2, 0.2])
    
    with col1:
        st.metric(label="学習した単語数", value=stats['total_words'])
    with col2:
        if stats['total_words'] > 0:
            st.metric(label="正答率", value=f"{stats['accuracy']}%")
        else:
            st.metric(label="正答率", value="-")
    with col3:
        st.metric(label="総出題回数", value=stats['correct_words'])
    
    # UI モード切り替え
    st.header("📚 TOEIC 単語学習アプリ")
    mode = st.radio(
        "モードを選択", 
        ["🍎 新しい単語", "📂 履歴・復習"],
        help="新しい単語を学習するか、過去の問題を復習します"
    )

    # ============================
    # 🎯 モード処理：新しい単語
    # ============================
    if mode == "🍎 新しい単語":
        st.subheader("今週の単語")
        
        # 最新の正解率を表示（DB にない場合の対策）
        try:
            stats = get_stats()
        except Exception as e:
            pass
            
        # セッション履歴管理
        if st.session_state.history_count < SESSION_LIMIT:
            try:
                conn = get_db_connection()
                
                # 最新の単語を取得（DB からランダム取得）
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM word_stats WHERE total_attempts > 0 ORDER BY RANDOM() LIMIT 1")
                row = cursor.fetchone()
                
                if row:
                    record_id = row['id']
                    target_word = row['word_text']
                    
                    # カラム存在チェック（DB 再構築時）
                    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='quiz_history'")
                    table_exists = cursor.fetchone() is not None
                    
                    if not table_exists:
                        try:
                            cursor.execute('''CREATE TABLE IF NOT EXISTS quiz_history (
                                id INTEGER PRIMARY KEY AUTOINCREMENT,
                                word_id INTEGER,
                                word_text TEXT,
                                translation_text TEXT,
                                user_answer TEXT,
                                correct_answer TEXT,
                                is_correct INTEGER DEFAULT 0,
                                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                            )''')
                        except:
                            pass
                    
                    cursor.execute("SELECT word_text, translation_text FROM quiz_history WHERE id=? LIMIT 1", (record_id,))
                    history = cursor.fetchone()
                    
                    if history:
                        target['word'] = history['word_text']
                        correct_answer = history['translation_text']
                    else:
                        # デフォルト値
                        st.session_state.word_text = target_word
                        st.session_state.correct_answer = ""
                        
                    conn.close()
                else:
                    st.info("学習用のデータが不足しています。CSV に追加してください。")
                    
            except Exception as e:
                st.error(f"⚠️ データベース操作エラー：{e}")

        # 回答入力欄（ユーザー入力）
        if 'user_answer' not in st.session_state:
            st.session_state.user_answer = ""
            
        # ユーザーの回答をキャプチャ（テキスト入力）
        user_input = st.text_area(
            "🎯 この単語の意味を入力", 
            key="user_answer_box", 
            help="日本語訳や同義語などを記入"
        )
        
        if st.button("✅ 確認"):
            is_correct = user_input == st.session_state.correct_answer
            
            # DB 更新（正解/不正解の記録）
            try:
                conn = get_db_connection()
                
                cursor.execute(f"""
                    UPDATE word_stats 
                    SET total_attempts = total_attempts + 1,
                        correct_attempts = CASE WHEN {int(is_correct)} THEN correct_attempts + 1 ELSE correct_attempts END
                    WHERE id = ?
                """, (record_id,))
                
                # 履歴テーブルへの記録
                cursor.execute(f"""
                    INSERT OR REPLACE INTO quiz_history 
                    (word_text, translation_text, user_answer, is_correct)
                    VALUES (?, ?, ?, ?)
                """, (st.session_state.word_text, st.session_state.correct_answer, user_input, int(is_correct)))
                
                conn.commit()
                st.success("回答を保存しました！")
            except Exception as e:
                st.error(f"⚠️ DB 更新エラー：{e}")

            # セッション状態更新
            st.session_state.history_count += 1
            st.session_state.user_answer = ""
            
        else:
            # 初期表示用（正解なし）
            st.session_state.correct_answer = "正解を表示するには「確認」ボタンを押してください"
            
        # 履歴管理（制限超過時はリセット）
        if st.session_state.history_count > SESSION_LIMIT and SESSION_LIMIT != -1:
