from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import json
import os
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

from utils.trie import build_trie
from utils.graph import Graph
from utils.stack import load_user_history_stack, save_user_history_stack

app = Flask(__name__, 
            template_folder='../frontend/templates', 
            static_folder='../frontend/static',
            static_url_path='/static')
app.secret_key = 'super_secret_key_for_smart_library'

DATA_DIR = os.path.join(os.path.dirname(__file__), 'data')
USERS_FILE = os.path.join(DATA_DIR, 'users.json')
BOOKS_FILE = os.path.join(DATA_DIR, 'books.json')
TRANSACTIONS_FILE = os.path.join(DATA_DIR, 'transactions.json')
PROGRESS_FILE = os.path.join(DATA_DIR, 'progress.json')
HISTORY_FILE = os.path.join(DATA_DIR, 'history.json')

# Global Data Structures
library_trie = None
library_graph = Graph()
books_list = []

def load_data(file_path, default_val=list):
    if not os.path.exists(file_path):
        return default_val()
    try:
        with open(file_path, 'r') as f:
            return json.load(f)
    except:
        return default_val()

def save_data(file_path, data):
    with open(file_path, 'w') as f:
        json.dump(data, f, indent=4)

def init_data_structures():
    global library_trie, library_graph, books_list
    books_list = load_data(BOOKS_FILE)
    library_trie = build_trie(books_list)
    library_graph.build_graph(books_list)

# Init DS on startup
init_data_structures()


### ROUTES ###

@app.route('/')
def root():
    if 'username' in session:
        return redirect(url_for('home'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        users = load_data(USERS_FILE)
        username = request.form['username']
        password = request.form['password']
        
        user = next((u for u in users if u['username'] == username), None)
        if user and check_password_hash(user['password'], password):
            session['username'] = username
            return redirect(url_for('home'))
        else:
            return render_template('login.html', error="Invalid credentials")
    
    return render_template('login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        users = load_data(USERS_FILE)
        username = request.form['username']
        password = request.form['password']
        
        if any(u['username'] == username for u in users):
            return render_template('signup.html', error="Username exists")
            
        new_user = {
            'username': username,
            'password': generate_password_hash(password)
        }
        users.append(new_user)
        save_data(USERS_FILE, users)
        
        # Init progress
        progress_data = load_data(PROGRESS_FILE, dict)
        progress_data[username] = {}
        save_data(PROGRESS_FILE, progress_data)
        
        return redirect(url_for('login'))
        
    return render_template('signup.html')

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('login'))

@app.route('/dashboard')
def home():
    if 'username' not in session: return redirect(url_for('login'))
    # Load recent activity
    user_stack = load_user_history_stack(HISTORY_FILE, session['username'])
    recent = user_stack.peek()
    return render_template('home.html', user=session['username'], recent=recent)

@app.route('/search')
def search():
    if 'username' not in session: return redirect(url_for('login'))
    return render_template('search.html')

@app.route('/api/search')
def api_search():
    query = request.args.get('q', '')
    if not query:
        return jsonify([])
    results = library_trie.search_prefix(query)
    return jsonify(results)

@app.route('/study-path')
def study_path():
    return render_template('study_path.html')

@app.route('/api/progress/update', methods=['POST'])
def update_progress():
    if 'username' not in session: return jsonify({"status":"error", "msg":"Unauthorized"})
    data = request.json
    book_id = data.get('book_id')
    status = data.get('status')
    
    progress_data = load_data(PROGRESS_FILE, dict)
    user_prog = progress_data.get(session['username'], {})
    user_prog[book_id] = status
    progress_data[session['username']] = user_prog
    save_data(PROGRESS_FILE, progress_data)
    return jsonify({"status":"success"})

@app.route('/recommend')
def recommend():
    if 'username' not in session: return redirect(url_for('login'))
    
    # Simple logic: get last issued/accessed book genre from stack
    user_stack = load_user_history_stack(HISTORY_FILE, session['username'])
    last = user_stack.peek()
    
    recs = []
    if last:
        book_id = last['book_id']
        recs = library_graph.get_recommendations(book_id)
    else:
        # Defaults to general top books
        recs = books_list[:5]
        
    return render_template('recommend.html', recommendations=recs)

@app.route('/history')
def history():
    if 'username' not in session: return redirect(url_for('login'))
    user_stack = load_user_history_stack(HISTORY_FILE, session['username'])
    return render_template('history.html', history=user_stack.get_all())

@app.route('/api/issue', methods=['POST'])
def issue_book():
    if 'username' not in session: return jsonify({"status":"error", "msg":"Unauthorized"})
    book_id = request.json.get('book_id')
    
    book = next((b for b in books_list if b['id'] == book_id), None)
    if not book or not book['available']:
        # If unavailable, find alternative from graph
        alt = library_graph.get_alternative(book_id)
        return jsonify({
            "status": "error", 
            "msg": "Book is unavailable.",
            "alternative": alt
        })
        
    # Mark as unavailable
    book['available'] = False
    save_data(BOOKS_FILE, books_list)
    
    # Reload Graph & Trie
    init_data_structures()
    
    # Add to transactions
    trans = load_data(TRANSACTIONS_FILE)
    t = {
        'id': str(len(trans)+1),
        'user': session['username'],
        'book_id': book_id,
        'book_title': book['title'],
        'action': 'ISSUE',
        'timestamp': datetime.now().isoformat()
    }
    trans.append(t)
    save_data(TRANSACTIONS_FILE, trans)
    
    # Push to User History Stack
    stack = load_user_history_stack(HISTORY_FILE, session['username'])
    stack.push(t)
    save_user_history_stack(HISTORY_FILE, session['username'], stack)
    
    return jsonify({"status":"success", "msg": f"Book '{book['title']}' issued successfully."})

@app.route('/api/return', methods=['POST'])
def return_book():
    if 'username' not in session: return jsonify({"status":"error", "msg":"Unauthorized"})
    book_id = request.json.get('book_id')
    
    book = next((b for b in books_list if b['id'] == book_id), None)
    if not book:
        return jsonify({"status": "error", "msg": "Book not found."})
        
    # Mark as available
    book['available'] = True
    save_data(BOOKS_FILE, books_list)
    init_data_structures()
    
    # Add to transactions
    trans = load_data(TRANSACTIONS_FILE)
    t = {
        'id': str(len(trans)+1),
        'user': session['username'],
        'book_id': book_id,
        'book_title': book['title'],
        'action': 'RETURN',
        'timestamp': datetime.now().isoformat()
    }
    trans.append(t)
    save_data(TRANSACTIONS_FILE, trans)
    
    # Push to User History Stack
    stack = load_user_history_stack(HISTORY_FILE, session['username'])
    stack.push(t)
    save_user_history_stack(HISTORY_FILE, session['username'], stack)
    
    return jsonify({"status":"success", "msg": f"Book '{book['title']}' returned successfully."})

import urllib.request
@app.route('/api/new_generate_pathway', methods=['POST'])
def new_generate_pathway():
    data = request.json
    level = data.get('level', 'Beginner')
    topics = data.get('topics', [])
    goal = data.get('goal', 'Just Learning')
    time_avail = data.get('time', '1-3 hrs/day')
    style = data.get('style', 'Mixed')
    api_key = data.get('api_key', '')
    
    # 1. Rule-based book matching mapping
    pathway = []
    
    for t in topics:
        t_lower = t.lower()
        topic_books = [b for b in books_list if t_lower in b.get('title', '').lower() or t_lower in b.get('genre', '').lower()]
        
        # filter by level
        level_books = [b for b in topic_books if b.get('level') == level]
        
        if not level_books:
            level_books = topic_books # fallback to any level if none perfectly matches
            
        if level_books:
            chosen_book = level_books[0]
            is_alt = False
            
            if not chosen_book.get('available', True):
                # Unavailable! Find alternative
                alt_book = library_graph.get_alternative(chosen_book['id'])
                if alt_book:
                    chosen_book = alt_book
                    is_alt = True
                else:
                    pass 
                
            pathway.append({
                "topic": t,
                "book": chosen_book,
                "is_alternative": is_alt
            })

    # If no books found at all, just fall back to some general books
    if not pathway:
        general_books = [b for b in books_list if b.get('level') == level]
        if general_books:
            b = general_books[0]
            alt = False
            if not b.get('available', True):
                b2 = library_graph.get_alternative(b['id'])
                if b2: b = b2; alt = True
            pathway.append({"topic": "General Foundation", "book": b, "is_alternative": alt})
            
    # 2. AI Enhancement
    ai_message = ""
    if api_key:
        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
            prompt = f"The student is a {level} learning {', '.join(topics)}. Their goal is {goal}. They learn {style} and have {time_avail}. Write a short, highly motivating 2-paragraph message guiding them, and estimating how long this path will take. Do not use markdown."
            payload = {"contents": [{"parts": [{"text": prompt}]}]}
            req = urllib.request.Request(url, data=json.dumps(payload).encode('utf-8'), headers={"Content-Type": "application/json"}, method='POST')
            with urllib.request.urlopen(req) as response:
                result = json.loads(response.read().decode('utf-8'))
                ai_message = result['candidates'][0]['content']['parts'][0]['text']
        except Exception as e:
            # Silently fail AI enhancement and just return the pathway
            pass
            
    return jsonify({
        "pathway": pathway,
        "ai_message": ai_message
    })

if __name__ == '__main__':
    app.run(debug=True, port=5000)
