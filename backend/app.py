from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import json
import os
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

from utils.trie import build_trie
from utils.graph import Graph
from utils.stack import load_user_history_stack, save_user_history_stack
from dotenv import load_dotenv
import os

load_dotenv()
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
ROADMAPS_FILE = os.path.join(DATA_DIR, 'roadmaps.json')

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
print("GEMINI KEY:", os.environ.get("GEMINI_API_KEY"))
@app.route('/api/new_generate_pathway', methods=['POST'])
def new_generate_pathway():
    data = request.json
    level = data.get('level', 'Beginner')
    topics = data.get('topics', [])
    goal = data.get('goal', 'Just Learning')
    time_avail = data.get('time', '1-3 hrs/day')
    style = data.get('style', 'Mixed')
    deadline = data.get('deadline', 'N/A')

    # 🔹 Filter books
    relevant_books = []
    topics_lower = [t.lower() for t in topics]
    goal_lower = goal.lower()

    for b in books_list:
        b_title = b.get('title', '').lower()
        b_genre = b.get('genre', '').lower()

        if (
            any(t in b_title or t in b_genre for t in topics_lower)
            or goal_lower in b_title
            or goal_lower in b_genre
        ):
            relevant_books.append(b)

    if not relevant_books:
        relevant_books = books_list[:5]

    relevant_books = relevant_books[:10]

    books_context = json.dumps([{
        "id": b.get("id"),
        "title": b.get("title"),
        "author": b.get("author", "Unknown"),
        "genre": b.get("genre", "")
    } for b in relevant_books])

    # 🔹 Prompt
    prompt = f"""
    You are an expert AI study planner. 
    The student wants to study exactly these topics: {', '.join(topics)}.
    Their primary goal is: {goal}.
    Skill level: {level}.
    Time availability: {time_avail}.

    Relevant books available in the library:
    {books_context}

    You MUST generate a highly structured roadmap.
    You MUST PRIORITIZE using the books from the library. Only add external resources if absolutely needed.
    You MUST respond with a valid JSON object strictly following this structure:
    {{
        "roadmap": [
            {{
                "week": "Week 1",
                "topics": "Primary topics covered",
                "subtopics": "Specific subtopics",
                "book_id": "Exact ID of the recommended library book from the context (e.g. '1', '42'). Must be a valid ID string. If absolutely no book fits perfectly, leave empty string.",
                "books": "Library books to use (Title by Author)",
                "resources": "External resources if needed",
                "tasks": "Specific tasks to complete",
                "outcome": "Expected outcome of the week"
            }}
        ],
        "final_section": {{
            "mistakes": "Common mistakes to avoid",
            "tips": "Tips for consistency",
            "motivation": "A highly motivating closing message"
        }}
    }}
    Do NOT wrap your response in markdown code blocks, just raw JSON.
    """

    try:
        api_key = os.environ.get("GEMINI_API_KEY", "").strip()

        if not api_key:
            return jsonify({"status": "error", "msg": "API key missing"}), 500

        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-flash-latest:generateContent?key={api_key}"

        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "responseMimeType": "application/json",
                "temperature": 0.7
            }
        }

        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode('utf-8'),
            headers={"Content-Type": "application/json"},
            method='POST'
        )

        with urllib.request.urlopen(req) as response:
            result = json.loads(response.read().decode('utf-8'))

        if 'candidates' not in result:
            return jsonify({"status": "error", "msg": "No response from AI."}), 500

        result_content = result['candidates'][0]['content']['parts'][0].get('text', '')
        result_json = json.loads(result_content)

        return jsonify({
            "status": "success",
            "data": result_json
        })

    except Exception as e:
        import traceback as tb
        import urllib.error as ue

        tb.print_exc()

        if isinstance(e, ue.HTTPError):
            try:
                error_body = e.read().decode('utf-8')
                print("Google API Error:", error_body)
                return jsonify({"status": "error", "msg": error_body}), 500
            except:
                pass

        return jsonify({"status": "error", "msg": str(e)}), 500

@app.route('/api/roadmap/active', methods=['GET'])
def get_active_roadmap():
    if 'username' not in session: return jsonify({"status":"error", "msg":"Unauthorized"})
    roadmaps = load_data(ROADMAPS_FILE, dict)
    user_roadmap = roadmaps.get(session['username'])
    if user_roadmap:
        return jsonify({"status": "success", "data": user_roadmap})
    return jsonify({"status": "success", "data": None})

@app.route('/api/roadmap/save', methods=['POST'])
def save_roadmap():
    if 'username' not in session: return jsonify({"status":"error", "msg":"Unauthorized"})
    data = request.json
    roadmap_data = {
        "current_step": 0,
        "roadmap": data.get('roadmap', []),
        "final_section": data.get('final_section', {})
    }
    roadmaps = load_data(ROADMAPS_FILE, dict)
    roadmaps[session['username']] = roadmap_data
    save_data(ROADMAPS_FILE, roadmaps)
    return jsonify({"status": "success"})

@app.route('/api/roadmap/exit', methods=['POST'])
def exit_roadmap():
    if 'username' not in session: return jsonify({"status":"error", "msg":"Unauthorized"})
    roadmaps = load_data(ROADMAPS_FILE, dict)
    if session['username'] in roadmaps:
        del roadmaps[session['username']]
        save_data(ROADMAPS_FILE, roadmaps)
    return jsonify({"status": "success"})

@app.route('/api/roadmap/issue_step', methods=['POST'])
def issue_step_book():
    if 'username' not in session: return jsonify({"status":"error", "msg":"Unauthorized"})
    roadmaps = load_data(ROADMAPS_FILE, dict)
    user_roadmap = roadmaps.get(session['username'])
    if not user_roadmap:
        return jsonify({"status": "error", "msg": "No active roadmap."})
    
    step_idx = user_roadmap.get('current_step', 0)
    roadmap_steps = user_roadmap.get('roadmap', [])
    if step_idx >= len(roadmap_steps):
        return jsonify({"status": "error", "msg": "Roadmap already completed."})
        
    step = roadmap_steps[step_idx]
    book_id = step.get('book_id')
    if not book_id:
        step['is_issued'] = True
        save_data(ROADMAPS_FILE, roadmaps)
        return jsonify({"status": "success", "msg": "Step started (no library book required)."})
        
    book = next((b for b in books_list if b['id'] == str(book_id)), None)
    if not book or not book.get('available', False):
        return jsonify({"status": "error", "msg": "Recommended book is unavailable. Please study theory or wait."})
        
    # Issue book
    book['available'] = False
    save_data(BOOKS_FILE, books_list)
    init_data_structures()
    
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
    
    stack = load_user_history_stack(HISTORY_FILE, session['username'])
    stack.push(t)
    save_user_history_stack(HISTORY_FILE, session['username'], stack)
    
    step['is_issued'] = True
    save_data(ROADMAPS_FILE, roadmaps)
    
    return jsonify({"status": "success", "msg": f"Book '{book['title']}' issued."})

@app.route('/api/roadmap/complete_step', methods=['POST'])
def complete_step():
    if 'username' not in session: return jsonify({"status":"error", "msg":"Unauthorized"})
    roadmaps = load_data(ROADMAPS_FILE, dict)
    user_roadmap = roadmaps.get(session['username'])
    if not user_roadmap:
        return jsonify({"status": "error", "msg": "No active roadmap."})
    
    step_idx = user_roadmap.get('current_step', 0)
    roadmap_steps = user_roadmap.get('roadmap', [])
    if step_idx >= len(roadmap_steps):
        return jsonify({"status": "error", "msg": "Roadmap already completed."})
        
    step = roadmap_steps[step_idx]
    book_id = step.get('book_id')
    
    if book_id and step.get('is_issued'):
        book = next((b for b in books_list if b['id'] == str(book_id)), None)
        if book:
            book['available'] = True
            save_data(BOOKS_FILE, books_list)
            init_data_structures()
            
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
            
            stack = load_user_history_stack(HISTORY_FILE, session['username'])
            stack.push(t)
            save_user_history_stack(HISTORY_FILE, session['username'], stack)
    
    user_roadmap['current_step'] = step_idx + 1
    step['is_completed'] = True
    save_data(ROADMAPS_FILE, roadmaps)
    return jsonify({"status": "success", "msg": "Step completed. Moved to next step."})

if __name__ == '__main__':

    app.run(debug=True, port=5000)