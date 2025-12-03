from flask import Flask, render_template, request, jsonify, session, redirect, url_for 
import sqlite3
import hashlib
import os
from datetime import datetime
from dotenv import load_dotenv
from groq import Groq

load_dotenv()

app = Flask(__name__)
app.secret_key = os.urandom(24)

# Load Groq API Key + Model
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
MODEL = os.getenv("MODEL_NAME", "llama-3.1-8b-instant")

# Initialize Groq Client
client = Groq(api_key=GROQ_API_KEY)


# ------------------- DATABASE -------------------------

def init_db():
    conn = sqlite3.connect('therabot.db')
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS chat_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            message TEXT NOT NULL,
            response TEXT NOT NULL,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')

    conn.commit()
    conn.close()

init_db()


def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()


def get_db_connection():
    conn = sqlite3.connect('therabot.db')
    conn.row_factory = sqlite3.Row
    return conn


# -------------------- ROUTES ----------------------------

@app.route('/')
def home():
    return render_template('index.html')


@app.route('/signin')
def signin_page():
    return render_template('signin.html')


@app.route('/signup')
def signup_page():
    return render_template('signup.html')


@app.route('/chat')
def chat_page():
    if 'user_id' not in session:
        return redirect(url_for('signin_page'))
    return render_template('chat.html')


# -------------------- SIGN UP ---------------------------

@app.route('/signup', methods=['POST'])
def signup():
    try:
        data = request.get_json()
        username = data.get('username', '').strip()
        password = data.get('password', '').strip()

        if not username or not password:
            return jsonify({'success': False, 'message': 'Username and password are required'})

        if len(password) < 6:
            return jsonify({'success': False, 'message': 'Password must be at least 6 characters long'})

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute('SELECT id FROM users WHERE username = ?', (username,))
        if cursor.fetchone():
            conn.close()
            return jsonify({'success': False, 'message': 'Username already exists'})

        password_hash = hash_password(password)
        cursor.execute('INSERT INTO users (username, password_hash) VALUES (?, ?)',
                       (username, password_hash))

        conn.commit()
        conn.close()

        return jsonify({'success': True, 'message': 'Account created successfully'})

    except Exception as e:
        return jsonify({'success': False, 'message': f'Server error occurred: {str(e)}'})


# -------------------- SIGN IN ---------------------------

@app.route('/signin', methods=['POST'])
def signin():
    try:
        data = request.get_json()
        username = data.get('username', '').strip()
        password = data.get('password', '').strip()

        if not username or not password:
            return jsonify({'success': False, 'message': 'Username and password are required'})

        conn = get_db_connection()
        cursor = conn.cursor()

        password_hash = hash_password(password)
        cursor.execute('SELECT id, username FROM users WHERE username = ? AND password_hash = ?',
                       (username, password_hash))
        user = cursor.fetchone()
        conn.close()

        if user:
            session['user_id'] = user['id']
            session['username'] = user['username']
            return jsonify({'success': True, 'message': 'Login successful'})
        else:
            return jsonify({'success': False, 'message': 'Invalid username or password'})

    except Exception as e:
        return jsonify({'success': False, 'message': f'Server error occurred: {str(e)}'})


# -------------------- CHAT BOT ---------------------------

@app.route('/api/chat', methods=['POST'])
def chat():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Please log in first'})

    try:
        data = request.get_json()
        user_message = data.get('message', '').strip()

        if not user_message:
            return jsonify({'success': False, 'message': 'Message cannot be empty'})

        system_instruction = (
            "You are a compassionate, empathetic, and non-judgmental digital therapist named Therabot. "
            "Your goal is to listen actively, provide emotional support, and gently guide users toward "
            "self-reflection and healthier coping strategies. Avoid giving medical advice. Encourage users "
            "to seek professional help for serious issues."
        )

        # -------------------- GROQ API CHAT ---------------------
        try:
            response = client.chat.completions.create(
                model=MODEL,
                messages=[
                    {"role": "system", "content": system_instruction},
                    {"role": "user", "content": user_message}
                ]
            )

            bot_response = response.choices[0].message.content

        except Exception as api_e:
            print("Groq API error:", api_e)
            bot_response = "I'm having trouble responding right now. Can you try again?"

        # Save in database
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            'INSERT INTO chat_history (user_id, message, response) VALUES (?, ?, ?)',
            (session['user_id'], user_message, bot_response)
        )
        conn.commit()
        conn.close()

        return jsonify({'success': True, 'response': bot_response})

    except Exception as e:
        return jsonify({'success': False, 'message': f'Server error occurred: {str(e)}'})


# -------------------- LOGOUT ----------------------------

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home'))


# -------------------- RUN APP ----------------------------

if __name__ == '__main__':
    app.run(debug=True, port=5000)
