import streamlit as st
import sqlite3
import pandas as pd
import csv
from datetime import datetime
import re
import os

# --- Configuration ---
DB_PATH = "quiz.db"
SESSION_LIMIT = 50

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    return conn

def init_db(conn):
    # Create Tables if they don't exist
    cursor = conn.cursor()
    
    # Word Stats table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS word_stats (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            word TEXT UNIQUE NOT NULL,
            definition TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # History table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS quiz_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT, -- Session ID to reset on logout or clear
            question_id INTEGER,
            is_correct BOOLEAN,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    conn.commit()

@st.cache_data
def fetch_words_from_db():
    conn = get_db_connection()
    df = pd.read_sql_query("SELECT * FROM word_stats ORDER BY id", conn)
    conn.close()
    return df.to_dict('records')

def add_csv_file(file, conn):
    if file is None:
        st.warning("No CSV file uploaded.")
        return
    
    try:
        # Use pandas to read csv safely
        raw_data = pd.read_csv(file)
        
        # Check for required columns (optional, but good for validation)
        required_cols = ['word', 'definition']
        
        if not all(col in raw_data.columns for col in required_cols):
            st.error(f"CSV must contain columns: {', '.join(required_cols)}")
            return

        # Insert into DB. Handle duplicates or updates.
        # Strategy: Replace existing rows with same word to keep it clean
        cursor = conn.cursor()
        
        for idx, row in raw_data.iterrows():
            word = str(row['word']).strip()
            definition = str(row.get('definition', '')).strip()
            
            # Use INSERT OR REPLACE pattern via parameterized query
            try:
                cursor.execute(
                    """INSERT OR REPLACE INTO word_stats (word, definition) 
                       VALUES (?, ?)""",
                    (word, definition)
                )
            except sqlite3.IntegrityError as e:
                st.error(f"Duplicate entry error during insert: {e}")
                # In production, handle this more gracefully if needed
        conn.commit()
        st.success(f"Successfully added {len(raw_data)} words.")
        
    except Exception as e:
        st.error(f"Error reading CSV: {e}")

def reset_quiz_history(session_id):
    """Reset history for current session."""
    if session_id is None: return
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Delete records with matching session ID to clear session data
    cursor.execute("""DELETE FROM quiz_history WHERE session_id = ?""", (session_id,))
    conn.commit()

def get_session_stats(conn):
    cursor = conn.cursor()
    # Get recent stats for dashboard
    cursor.execute("SELECT COUNT(*) as count, SUM(is_correct) as correct_count FROM quiz_history GROUP BY session_id") 
    return cursor.fetchall()

# --- Streamlit UI ---
st.set_page_config(
    page_title="Vocabulary Quiz App",
    layout="wide"
)

# Initialize Session State
if 'session_started' not in st.session_state:
    st.session_state['session_started'] = False
if 'session_id' not in st.session_state:
    st.session_state['session_id'] = str(datetime.now().timestamp()) # Unique per session reload

st.title("🇯🇵 English Vocabulary Quiz")
st.markdown("---")

# --- Sidebar for Admin/History ---
with st.sidebar:
    st.header("Settings & History")
    
    # File Upload
    uploaded_file = st.file_uploader("Upload CSV (word, definition)", type=['csv'])
    if uploaded_file:
        add_csv_file(uploaded_file, get_db_connection())

    st.divider()
    
    # Reset History Button
    reset_btn = st.button("Reset Quiz History", key="reset_history")
    if reset_btn and not st.session_state['session_started']:
        st.toast("History reset.", icon="🔄")
        reset_quiz_history(st.session_state['session_id'])

# --- Main Content ---

st.header("Dashboard")

# Dashboard Section: Recent Stats (Optional, might need specific DB setup to show)
# For simplicity and robustness without external services, we can just show status.

with st.expander("See Database Records"):
    words = fetch_words_from_db()
    if words:
        df_display = pd.DataFrame(words, columns=['id', 'word', 'definition', 'created_at'])
        # Drop internal id for display
        display_df = df_display[['word', 'definition']].sort_values('word')
        st.dataframe(display_df, use_container_width=True)
    else:
        st.info("No words in database. Please upload a CSV file to get started.")

st.divider()

# --- Quiz Game Section ---
if not st.session_state['session_started']:
    st.write("""
    **Welcome!** This is your vocabulary quiz session.
    
    Rules:
    1. Read the English definition provided.
    2. Type the Japanese word matching that definition into the input box.
    3. Click "Submit" to check your answer.
    4. Click "Next Word" to continue.
    """)

    col_input, col_submit = st.columns([3, 1])
    
    with col_input:
        # Fetch all words from DB for this round (or limit if needed)
        raw_words = fetch_words_from_db() 
        if not raw_words:
            st.warning("No questions available. Please upload a CSV file.")
        else:
            # Simplest quiz: Randomize and show one per turn, or cycle through
            # Using session state for current index
            
            current_idx = st.session_state.get('current_word_index', 0)
            
            if len(raw_words) > 0:
                current_word = raw_words[current_idx]
                
                st.subheader(f"Word {current_idx + 1}")
                correct_def = current_word['definition']
                # Note: In the previous code, 'word' was English and 'definition' Japanese. 
                # But based on typical Quiz structure: Input is usually target language (Japanese).
                # I will assume Target: Japanese -> Prompt: English Definition
                
                st.write(f"Translate to Japanese:")
                st.info(correct_def) # Actually the previous code had "word" as EN, "definition" as JP. 
                # Let's standardise:
                # If 'word' is English and 'definition' is Japanese (per typical dictionary):
                # But user input logic in prompt was: Input Box -> Answer Check.
                
                # Re-reading the prompt logic:
                # "Input Box" -> User types answer. 
                # Correct answer check against database "definition" column? Or "word"?
                
                # Let's assume:
                # DB Column 'word' = English Word.
                # DB Column 'definition' = Japanese Meaning (or vice versa).
                
                # For clarity, let's use 'word' as the target language (Japanese) to type into box?
                # Actually, usually it's EN -> JP.
                # Let's assume user types in English (if DB is JP->EN) or JP (if DB is EN->JP).
                
                # I will standardise: 
                # Input Box expects 'word' column content from DB.
                # Prompt displays 'definition'.
                target = current_word.get('word')
                hint = current_word.get('definition')
                
                user_answer = st.text_input("Type your answer here:", key=f"input_{current_idx}")
                
                with col_submit:
                    submit_btn = st.button("Check Answer", key=f"submit_{current_idx}")

        if submit_btn:
            # Check Logic
            # Ensure we don't index out of bounds
            if len(raw_words) > current_idx and user_answer.lower().strip() == target.lower().strip():
                st.success(f"✅ Correct! The answer is '{target}'.")
                # Record success in DB
                try:
                    conn = get_db_connection()
                    cursor = conn.cursor()
                    cursor.execute("INSERT INTO quiz_history (session_id, question_id, is_correct) VALUES (?, ?, ?)", 
                                   (st.session_state['session_id'], current_idx + 1, 1))
                    conn.commit()
                except Exception as e:
                    print(f"DB Insert failed silently: {e}")
                
                # Advance index
                st.session_state['current_word_index'] = (current_idx + 1) % len(raw_words)
            else:
                st.error(f"❌ Incorrect. Correct answer: '{target}'.")

else:
    # Session has "started" logic in previous snippets was weird. 
    # I will remove the state flag and just handle the session ID reset via the sidebar or clear button?
    # Actually, Streamlit runs once per file load. State persists until reload.
    # So 'session_started' is to track if user hit a "Start" button.
    pass

# --- Footer ---
st.markdown("---")

