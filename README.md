# Smart Library Management System 📚✨

A modern, intelligent, and scalable Library Management Web Application built with Python Flask, powerful custom data structures, and a premium Tailwind CSS aesthetic.

## 🌟 Features

- **Authentication System**: Secure user signup and login with hashed session-based authentication.
- **Smart Book Search**: Blazing fast search using a custom **Trie** data structure for autocomplete functionality.
- **Issue & Return**: Seamless book transaction system with dynamic status updates.
- **Recommendation Engine**: Intelligent suggestions powered by a **Graph** data structure that links books based on genres and themes, offering smart alternatives when a book is unavailable.
- **History Tracking**: Keep track of user reading timelines utilizing a **Stack (LIFO)** data structure.
- **Structured Study Paths**: Visually tracking your growth across levels (Beginner, Intermediate, Advanced) in domains like DSA, AI, and Mathematics.
- **Modern UI/UX**: Designed with a Glassmorphism aesthetic, rich hover effects, micro-animations, built-in light/dark themes, and responsive design.

---

## 💻 Tech Stack

- **Frontend**: HTML5, CSS3, JavaScript (Vanilla), Tailwind CSS (Premium modern layout).
- **Backend**: Python, Flask (Robust REST APIs and templating).
- **Database**: Local JSON based datastores (`users.json`, `books.json`, `transactions.json`, `progress.json`, `history.json`) for seamless setup without external dependencies.
- **Security**: Werkzeug password hashing.

---

## 🧠 Data Structures Used

This application proudly employs core data structures for optimized operations:

1. **Trie** → Resolves O(L) fast prefix lookups for the Book Search Engine, enabling instant UI auto-complete.
2. **Graph** → Connects related genres and books into an adjacency list to form our Recommender System.
3. **Stack** → Operates the User History system with purely Last-In-First-Out processing to display chronological context optimally.

---

## 📁 Project Structure

```
slibrary/
│
├── app.py                  # Core Flask Application & API Routes
├── requirements.txt        # Python Dependencies
├── README.md               # Project Documentation
│
├── static/
│   ├── css/styles.css      # Custom animations and variables
│   └── js/main.js          # Core API fetch logic & Theme toggling
│
├── templates/              # Jinja2 HTML Templates
│   ├── base.html           # Layout wrapper
│   ├── home.html           # Dashboard
│   ├── login.html          # Authentication Views
│   ├── signup.html
│   ├── search.html         # Trie Search View
│   ├── history.html        # Stack History View
│   ├── recommend.html      # Graph Recommender View
│   └── study_path.html     # Structured Path View
│
├── data/                   # JSON "NoSQL" datastores
│   ├── users.json
│   ├── books.json
│   ├── transactions.json
│   ├── progress.json
│   └── history.json
│
└── utils/                  # Core Algorithmic Logic
    ├── trie.py
    ├── graph.py
    └── stack.py
```

---

## 🚀 Setup Instructions

1. **Clone the Repository**
   ```bash
   git clone https://github.com/your-username/smart-library.git
   cd smart-library
   ```

2. **Create a Virtual Environment (Optional but recommended)**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the Application**
   ```bash
   python app.py
   ```

5. **Access the App**
   Open your browser and navigate to `http://127.0.0.1:5000`

---

## 📸 Screenshots

*(Replace placeholder text with actual screenshots once deployed)*

1. **Login Dashboard**
   *(Image showing the glassmorphism authentication view)*
2. **Main Dashboard**
   *(Image showing recent activity and statistics)*
3. **Search System**
   *(Image showing dynamic Trie autocomplete in action)*
4. **Study Path**
   *(Image showing locked/unlocked progress nodes)*

---

## 🔮 Future Improvements

- Migrate from JSON storage to PostgreSQL/MongoDB for enterprise production.
- Add Admin Dashboard to view global analytics and manage books.
- Add Email Notifications for overdue returns.
- Include Advanced analytics graphs on the Dashboard using Chart.js.

---

*Built with ❤️ for a structured understanding of CS Data Structures in Web Development.*
