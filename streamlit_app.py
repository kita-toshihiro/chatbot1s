import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime
import os

# ==========================================
# 設定・初期化処理 (ランタイムで実行)
# ==========================================

# データベースファイル名
DB_FILE = "study.db"
WORD_CSV = "words.csv"
SESSION_HISTORY_LIMIT = 5 # 1 セッションあたりの出題数制限（オプション）

def init_db():
    """DB 初期化関数"""
    if not os.path.exists(DB_FILE):
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        
        # 単語テーブル（一応の念のため、CSV から読み込ませるため DB 内の管理用テーブルも作ります）
        """ 
           もし words.csv を直接参照するなら history に id を入れるだけなので、
           CSV ファイルの行番号を ID として扱います。
        """

        c.execute('''
            CREATE TABLE IF NOT EXISTS quiz_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                word_id INTEGER NOT NULL,
                word_text TEXT NOT NULL,
                translation_text TEXT NOT NULL, # ユーザーが入力した内容
                correct_answer TEXT NOT NULL,   # 正解の日本語訳
                is_correct BOOLEAN NOT NULL,    # 正答判定
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # 統計用テーブル（復習モードで使いやすいように）
        c.execute('''
            CREATE TABLE IF NOT EXISTS word_stats (
                id INTEGER PRIMARY KEY,
                word_text TEXT UNIQUE NOT NULL,
                total_attempts INTEGER DEFAULT 0,
                correct_attempts INTEGER DEFAULT 0
            )
        ''')
        
        conn.commit()
        conn.close()

def load_words():
    """CSV から単語リストをロード（DB を参照する場合の補助情報も持てば良いが、シンプルに CSV の row_id で管理）"""
    if not os.path.exists(WORD_CSV):
        st.error("❌ words.csv というファイルが見つかりません。")
        return pd.DataFrame()

    try:
        df = pd.read_csv(WORD_CSV)
        
        # CSV の列指定（もし header がなかった場合は colnames を確認）
        # ここでは 'word' と 'meaning' があると仮定します
        if 'id' not in df.columns and 'word' not in df.columns:
            st.error("❌ words.csv のカラム名が 'id', 'word', 'meaning' でありません。")
            return pd.DataFrame()
        
        return df.reset_index(drop=True) # 0 から始まる index を ID として扱うためリセット
        
    except Exception as e:
        st.error(f"❌ CSV 読み込みエラー：{e}")
        return pd.DataFrame()

def check_word_correct(input_text, correct_answer):
    """文字列照合（スペーストリム）"""
    if input_text.lower().strip() == correct_answer.strip():
        return True
    return False

# ==========================================
# メインアプリロジック
# ==========================================

st.set_page_config(page_title="TOEIC Vocab", layout="centered")
st.header("🎯 TOEIC 600 点単語マスター (Streamlit + SQLite)")

init_db()

# --- セッション管理 (St.session_state) ---
if 'quiz_data' not in st.session_state:
    # アプリ開始時（ファイル読み込み）
    # CSV を直接使うため、DB に格納した履歴データは session_state 内に持たな
いが、
    # ユーザー入力部分は Session State で保持する
    
    # CSV の列名を確定させる
    if os.path.exists(WORD_CSV):
        df_temp = pd.read_csv(WORD_CSV)
        st.session_state.df_data = df_temp.to_dict('records')
    
# 1. アプリのタブまたはモード選択
menu = st.sidebar.title("メニュー")
# sidebartab (Streamlit Community Cloud ではシンプルにサイドバーボタン)

mode, _ = st.tabs(["📝 単語学習", "📂 履歴・復習"])

if mode == "📝 単語学習":
    # --- クイズ部分 ---
    
    if len(st.session_state.df_data) == 0:
        st.error("データの準備ができていません。")
    else:
        st.subheader(f"現在の単語数：{len(st.session_state.df_data)} 語")

        # ランダム選択 (SessionState で保持する現在のクイズ用データ)
        if 'current_word' not in st.session_state or 'history_count' not in st.session_state:
            st.session_state.history_count = 0
            import random
            # ランダムな単語を選択（セッションに格納）
            target_id = random.randint(0, len(st.session_state.df_data) - 1)
            w = st.session_state.df_data[target_id]
            st.session_state.current_word = {
                "id": w['id'],
                "word": w['word'],
                "meaning": w['meaning']
            }

        # クイズ表示
        target = st.session_state.current_word
        st.success(f"Q. #{st.session_state.history_count + 1}")
        
        col_question, col_answer = st.columns([2, 1])
        
        with col_question:
            # 表示用
            st.markdown(f"**{target['word']}**")
            st.write("_______（意味を当ててください）")

        with col_answer:
            user_input = st.text_input("日本語訳:", key="user_input")
            
            if st.button("チェックする"):
                # 正答判定
                is_correct = check_word_correct(user_input, target['meaning'])
                
                # UI Feedback
                if is_correct:
                    st.success(f"✅ 正解でした！ ({target['meaning']})")
                else:
                    st.error(f"❌ 不正解。正解は：{target['meaning']}")
                
                # DB に記録（SQLite）
                conn = sqlite3.connect(DB_FILE)
                cur = conn.cursor()
                record_id = target['id']
                now = datetime.now().isoformat()
                
                # 履歴保存
                sql = f"""
                    INSERT INTO quiz_history (word_id, word_text, translation_text, correct_answer, is_correct, created_at)
                    VALUES ({record_id}, "{target['word']}", "{user_input}", "{target['meaning']}", {is_correct}, "{now}")
                """
                cur.execute(sql)
                
                # 統計テーブル更新（総数・正答数の加算）
                # word_stats テーブルを作成し、既存単語の集計を更新
                try:
                    cur.execute(f"""
                        UPDATE word_stats 
                        SET total_attempts = total_attempts + 1,
                            correct_attempts = CASE WHEN {is_correct} THEN correct_attempts + 1 ELSE correct_attempts END
                        WHERE id = {record_id}
                    """)
                except Exception as e:
                    # カラムが存在しない場合（DB 再構築のタイミング）
                    try:
                        cur.execute(f"""
                            INSERT OR IGNORE INTO word_stats (id, word_text, total_attempts, correct_attempts)
                            VALUES ({record_id}, "{target['word']}", 1, {int(is_correct)})
                        """)
                    except Exception as e2:
                        pass # カラム追加エラー

                conn.commit()
                
                st.session_state.history_count += 1
                
                # セッションで最大出題数制限（例：5 問）を設けるかどうか？
                if st.session_state.history_count >= SESSION_HISTORY_LIMIT and SESSION_HISTORY_LIMIT > 0:
                    st.warning("本日の学習完了です。")
                    
        # リセットボタンの表示（次の単語を表示したい場合）
        if st.session_state.history_count > 0:
            st.button("次へ（新しい単語を表示）", on_click=lambda: None, key='fake_reset') # ダミーボタン
            
        # 履歴からエクスポートさせるためのボタン（本日の結果だけ？）
        pass 

elif mode == "📂 履歴・復習":
    st.subheader("学習の振り返り")

    conn = sqlite3.connect(DB_FILE)
    
    # SQL クエリ：全ての結果をフェッチ
    query_all = """
        SELECT word_id, word_text, translation_text, correct_answer, is_correct 
        FROM quiz_history 
        ORDER BY created_at DESC;
    """
    
    try:
        df_history = pd.read_sql_query(query_all, conn)
        
        if not df_history.empty:
            st.dataframe(df_history)

            # 学習ミス（不正解）の抽出ボタン
            with st.expander("❌ ミスだけを復習したい"):
                query_mistakes = """
                    SELECT word_text, translation_text, correct_answer 
                    FROM quiz_history 
                    WHERE is_correct = 0;
                """
                df_mistake = pd.read_sql_query(query_mistakes, conn)
                
                if not df_mistake.empty:
                    st.error(f"学習ミス：{len(df_mistake)} 語")
                    st.dataframe(df_mistake)
                    
                    # エクスポートボタン（CSV に書き出し）
                    csv_data = df_mistake.to_csv(index=False).encode('utf-8')
                    st.download_button(
                        label="📥 ミスだけを CSV で保存",
                        data=csv_data,
                        file_name="mistakes_to_review.csv",
                        mime="text/csv"
                    )
                else:
                    st.success("学習ミスはありません。完璧です！")

        else:
            st.info("履歴データがありません。まずは「単語学習」を行ってください。")

    except Exception as e:
        st.error(f"DB 読み込みエラー：{e}")
        
        # エクスポート機能のバッチ処理（CSV で手動書き出し）
        with st.expander("💾 全履歴を CSV にダウンロード"):
            df_csv = pd.read_csv(WORD_CSV) 
            # ここで DB のデータと CSV を結合して渡したいが、今回は簡易対応

            pass

# 終了画面表示用
st.markdown("---")
st.caption(f"Powered by Streamlit + SQLite3")
