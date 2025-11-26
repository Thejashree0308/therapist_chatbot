from flask import Flask, render_template, request, jsonify, session, redirect, url_for
import sqlite3
import hashlib
import os
from datetime import datetime
from google import genai
from dotenv import load_dotenv

load_dotenv()  


app = Flask(__name__)
app.secret_key = 'your-secret-key-change-this-in-production' 
GOOGLE_GENAI_API_KEY = os.getenv("GOOGLE_GENAI_API_KEY")
# Google GenAI client
client = genai.Client(api_key=GOOGLE_GENAI_API_KEY)

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

@app.route('/api/chat', methods=['POST'])
def chat():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Please log in first'})

    try:
        data = request.get_json()
        user_message = data.get('message', '').strip()

        if not user_message:
            return jsonify({'success': False, 'message': 'Message cannot be empty'})
        bot_response = ""
        try:
            system_instruction = "You are a compassionate, empathetic, and non-judgmental digital therapist named Therabot. Your goal is to listen actively, provide emotional support, and gently guide users towards self-reflection and coping strategies. Avoid giving direct medical advice. Always encourage users to seek professional help for serious issues. Keep responses concise but helpful."


            response = client.models.generate_content(
                model = 'gemini-2.0-flash',
                contents=system_instruction + "\n\nUser: " + user_message
            )
            bot_response = response.text
            print(f"Bot response: {bot_response}")

        except Exception as api_e:
            print(f"Error calling Gemini API: {api_e}")
            bot_response = "I'm sorry, I'm having trouble connecting to my thoughts right now. Could you please rephrase or try again?"
        

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('INSERT INTO chat_history (user_id, message, response) VALUES (?, ?, ?)',
                      (session['user_id'], user_message, bot_response))
        conn.commit()
        conn.close()

        return jsonify({'success': True, 'response': bot_response})

    except Exception as e:
        return jsonify({'success': False, 'message': f'Server error occurred: {str(e)}'})

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home'))

if __name__ == '__main__':
    if not app.secret_key or app.secret_key == 'your-secret-key-change-this-in-production':
        print("WARNING: Please change app.secret_key to a strong, random value for production.")
        app.secret_key = os.urandom(24)

    app.run(debug=True, port=5000)
    print(genai.__version__)