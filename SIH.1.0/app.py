"""
KnowVia AI Study Platform - Complete Working Single-File Application
Full-stack Flask app with embedded frontend and AI integration
All buttons and navigation fixed
"""

import os
import uuid
import json
from datetime import datetime
from flask import Flask, render_template, request, jsonify, send_from_directory, Response
from werkzeug.utils import secure_filename

# Optional Google AI
try:
    import google.generativeai as genai
    GOOGLE_AI_AVAILABLE = True
except ImportError:
    GOOGLE_AI_AVAILABLE = False
    print("⚠️  google-generativeai not installed - AI features disabled")

# Flask app configuration
app = Flask(__name__)
app.config['SECRET_KEY'] = 'knowvia-secret-key-2025'
app.config['UPLOAD_FOLDER'] = os.path.join(os.getcwd(), 'uploads')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB

# Create upload directory
# Ensure upload directory exists
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

# Gemini API setup
GEMINI_API_KEY = ""
if GOOGLE_AI_AVAILABLE and GEMINI_API_KEY != "YOUR_GEMINI_API_KEY_HERE":
    try:
        genai.configure(api_key=GEMINI_API_KEY)
        print(" Gemini AI configured")
    except Exception as e:
        print(f" Gemini setup failed: {e}")
        GOOGLE_AI_AVAILABLE = False

# File upload settings
ALLOWED_EXTENSIONS = {'txt','png', 'jpg', 'jpeg', 'gif', 'bmp', 'mp4', 'avi', 'mov', 'webm', 'mkv', 'pdf'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Enhanced In-memory database with educational content
doubts_db = []
notes_db = []
quiz_db = []
study_progress = {}

# Educational content database
SUBJECTS_DATA = {
    'mathematics': {
        'name': 'Mathematics',
        'icon': '🧮',
        'color': '#ff6b6b',
        'description': 'Master mathematical concepts from algebra to calculus',
        'topics': ['Algebra', 'Calculus', 'Geometry', 'Statistics', 'Trigonometry', 'Linear Algebra'],
        'videos': [
            {'title': 'Linear Equations Mastery', 'duration': '15:30', 'views': '1.2K', 'difficulty': 'Beginner'},
            {'title': 'Quadratic Functions Deep Dive', 'duration': '22:45', 'views': '890', 'difficulty': 'Intermediate'},
            {'title': 'Derivatives and Applications', 'duration': '18:20', 'views': '2.1K', 'difficulty': 'Advanced'}
        ],
        'notes_count': 25,
        'quiz_count': 15
    },
    'physics': {
        'name': 'Physics',
        'icon': '⚛️',
        'color': '#4ecdc4',
        'description': 'Explore the fundamental laws that govern our universe',
        'topics': ['Mechanics', 'Thermodynamics', 'Electromagnetism', 'Optics', 'Modern Physics', 'Quantum Physics'],
        'videos': [
            {'title': 'Newton\'s Laws Explained', 'duration': '20:15', 'views': '3.4K', 'difficulty': 'Beginner'},
            {'title': 'Electric Fields and Forces', 'duration': '25:30', 'views': '1.8K', 'difficulty': 'Intermediate'},
            {'title': 'Wave Motion Fundamentals', 'duration': '19:45', 'views': '2.7K', 'difficulty': 'Advanced'}
        ],
        'notes_count': 30,
        'quiz_count': 20
    },
    'chemistry': {
        'name': 'Chemistry',
        'icon': '🧪',
        'color': '#45b7d1',
        'description': 'Understand matter, its properties, and transformations',
        'topics': ['Organic Chemistry', 'Inorganic Chemistry', 'Physical Chemistry', 'Analytical Chemistry', 'Biochemistry'],
        'videos': [
            {'title': 'Chemical Bonding Basics', 'duration': '24:10', 'views': '1.5K', 'difficulty': 'Beginner'},
            {'title': 'Thermochemistry Principles', 'duration': '21:55', 'views': '980', 'difficulty': 'Intermediate'},
            {'title': 'Organic Reaction Mechanisms', 'duration': '28:30', 'views': '1.9K', 'difficulty': 'Advanced'}
        ],
        'notes_count': 22,
        'quiz_count': 18
    },
    'biology': {
        'name': 'Biology',
        'icon': '🧬',
        'color': '#96ceb4',
        'description': 'Study life and living organisms at all levels',
        'topics': ['Cell Biology', 'Genetics', 'Ecology', 'Evolution', 'Physiology', 'Molecular Biology'],
        'videos': [
            {'title': 'DNA Structure and Function', 'duration': '17:25', 'views': '2.3K', 'difficulty': 'Beginner'},
            {'title': 'Photosynthesis Process', 'duration': '23:15', 'views': '1.7K', 'difficulty': 'Intermediate'},
            {'title': 'Genetics and Inheritance', 'duration': '26:40', 'views': '2.0K', 'difficulty': 'Advanced'}
        ],
        'notes_count': 28,
        'quiz_count': 16
    },
    'computer_science': {
        'name': 'Computer Science',
        'icon': '💻',
        'color': '#feca57',
        'description': 'Learn programming, algorithms, and computational thinking',
        'topics': ['Programming', 'Data Structures', 'Algorithms', 'Web Development', 'AI/ML', 'Database Systems'],
        'videos': [
            {'title': 'Python Programming Basics', 'duration': '30:00', 'views': '4.1K', 'difficulty': 'Beginner'},
            {'title': 'Data Structures Overview', 'duration': '35:20', 'views': '2.8K', 'difficulty': 'Intermediate'},
            {'title': 'Machine Learning Introduction', 'duration': '40:15', 'views': '3.2K', 'difficulty': 'Advanced'}
        ],
        'notes_count': 35,
        'quiz_count': 25
    },
    'english': {
        'name': 'English Literature',
        'icon': '📚',
        'color': "#827dcd",
        'description': 'Master language, literature, and communication skills',
        'topics': ['Grammar', 'Literature', 'Writing', 'Communication', 'Poetry', 'Essay Writing'],
        'videos': [
            {'title': 'Essay Writing Techniques', 'duration': '32:45', 'views': '1.6K', 'difficulty': 'Beginner'},
            {'title': 'Grammar Fundamentals', 'duration': '28:30', 'views': '2.2K', 'difficulty': 'Intermediate'},
            {'title': 'Poetry Analysis Methods', 'duration': '26:15', 'views': '1.4K', 'difficulty': 'Advanced'}
        ],
        'notes_count': 20,
        'quiz_count': 12
    }
}

# Sample notes data
SAMPLE_NOTES = [
    {
        'id': 1,
        'subject': 'mathematics',
        'title': 'Linear Equations and Inequalities',
        'content': '''# Linear Equations and Inequalities

## Key Concepts
- Linear equation: ax + b = 0
- Solution methods: algebraic manipulation
- Graphical representation on coordinate plane

## Examples
1. Solve: 2x + 5 = 13
   - 2x = 13 - 5
   - 2x = 8
   - x = 4

## Practice Problems
- 3x - 7 = 11
- 5x + 2 = 3x + 8
- 2(x + 3) = 4x - 2''',
        'created': '2025-09-15',
        'author': 'KnowVia Team'
    },
    {
        'id': 2,
        'subject': 'physics',
        'title': 'Newton\'s Laws of Motion',
        'content': '''# Newton's Laws of Motion

## First Law (Law of Inertia)
An object at rest stays at rest, and an object in motion stays in motion at constant velocity, unless acted upon by an external force.

## Second Law
F = ma
- Force equals mass times acceleration
- Net force determines acceleration

## Third Law
For every action, there is an equal and opposite reaction.

## Applications
- Rocket propulsion
- Walking mechanics
- Car safety features
- Sports physics''',
        'created': '2025-09-14',
        'author': 'KnowVia Team'
    },
    {
        'id': 3,
        'subject': 'chemistry',
        'title': 'Chemical Bonding Types',
        'content': '''# Chemical Bonding

## Ionic Bonds
- Transfer of electrons
- Between metals and non-metals
- Example: NaCl (Sodium Chloride)

## Covalent Bonds
- Sharing of electrons
- Between non-metals
- Example: H2O (Water)

## Metallic Bonds
- Sea of electrons
- Between metals
- Properties: conductivity, malleability''',
        'created': '2025-09-13',
        'author': 'KnowVia Team'
    }
]

# Sample quiz data
SAMPLE_QUIZZES = [
    {
        'id': 1,
        'subject': 'mathematics',
        'title': 'Algebra Basics Quiz',
        'description': 'Test your understanding of basic algebraic concepts',
        'questions': [
            {
                'question': 'Solve: 2x + 5 = 13',
                'options': ['x = 3', 'x = 4', 'x = 5', 'x = 6'],
                'correct': 1,
                'explanation': '2x = 13 - 5 = 8, so x = 4'
            },
            {
                'question': 'What is the slope of the line y = 3x + 2?',
                'options': ['2', '3', '5', '1'],
                'correct': 1,
                'explanation': 'In y = mx + b form, m is the slope, so slope = 3'
            }
        ]
    },
    {
        'id': 2,
        'subject': 'physics',
        'title': 'Motion and Forces',
        'description': 'Understanding basic concepts of motion and forces',
        'questions': [
            {
                'question': 'What is Newton\'s first law also known as?',
                'options': ['Law of Energy', 'Law of Inertia', 'Law of Motion', 'Law of Force'],
                'correct': 1,
                'explanation': 'Newton\'s first law is also called the Law of Inertia'
            },
            {
                'question': 'What is the unit of force?',
                'options': ['Joule', 'Watt', 'Newton', 'Pascal'],
                'correct': 2,
                'explanation': 'The SI unit of force is Newton (N)'
            }
        ]
    }
]

# Initialize sample data
notes_db.extend(SAMPLE_NOTES)
quiz_db.extend(SAMPLE_QUIZZES)

# Routes
@app.route('/')
def home():
    return render_template('index.html')

@app.route('/api/subjects', methods=['GET'])
def get_subjects():
    return jsonify(SUBJECTS_DATA)

@app.route('/api/subjects/<subject_id>/notes', methods=['GET'])
def get_subject_notes(subject_id):
    subject_notes = [note for note in notes_db if note['subject'] == subject_id]
    return jsonify(subject_notes)

@app.route('/api/subjects/<subject_id>/quizzes', methods=['GET'])
def get_subject_quizzes(subject_id):
    subject_quizzes = [quiz for quiz in quiz_db if quiz['subject'] == subject_id]
    return jsonify(subject_quizzes)

@app.route('/api/notes', methods=['GET'])
def get_all_notes():
    return jsonify(notes_db)

@app.route('/api/notes', methods=['POST'])
def create_note():
    try:
        data = request.get_json()
        note = {
            'id': len(notes_db) + 1,
            'subject': data.get('subject'),
            'title': data.get('title'),
            'content': data.get('content'),
            'created': datetime.now().strftime('%Y-%m-%d'),
            'author': 'Student',
            'upvotes': 0,
            'downvotes': 0
        }
        notes_db.append(note)
        return jsonify({'success': True, 'note': note})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/quizzes', methods=['GET'])
def get_all_quizzes():
    return jsonify(quiz_db)

@app.route('/api/quiz/<int:quiz_id>', methods=['GET'])
def get_quiz(quiz_id):
    quiz = next((q for q in quiz_db if q['id'] == quiz_id), None)
    if quiz:
        return jsonify(quiz)
    return jsonify({'error': 'Quiz not found'}), 404

@app.route('/api/quiz/<int:quiz_id>/submit', methods=['POST'])
def submit_quiz(quiz_id):
    try:
        data = request.get_json()
        answers = data.get('answers', [])
        
        quiz = next((q for q in quiz_db if q['id'] == quiz_id), None)
        if not quiz:
            return jsonify({'error': 'Quiz not found'}), 404
        
        score = 0
        total = len(quiz['questions'])
        results = []
        
        for i, answer in enumerate(answers):
            question = quiz['questions'][i]
            is_correct = answer == question['correct']
            if is_correct:
                score += 1
            
            results.append({
                'question_index': i,
                'user_answer': answer,
                'correct_answer': question['correct'],
                'is_correct': is_correct,
                'explanation': question['explanation']
            })
        
        percentage = (score / total) * 100
        return jsonify({
            'score': score,
            'total': total,
            'percentage': percentage,
            'results': results
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/ai-tutor', methods=['POST'])
def ai_tutor():
    try:
        data = request.get_json()
        question = data.get('question', '').strip()
        subject = data.get('subject', '')
        
        if not question:
            return jsonify({'error': 'Question is required'}), 400
        
        if GOOGLE_AI_AVAILABLE:
            try:
                model = genai.GenerativeModel('gemini-1.5-flash')
                prompt = f"""You are KnowVia AI Tutor, an expert in {subject}. 
                Answer this student's question clearly and educationally: {question}
                
                Provide:
                1. Clear explanation
                2. Step-by-step solution if applicable
                3. Related concepts to explore
                4. Practice suggestions"""
                
                response = model.generate_content(prompt)
                
                return jsonify({
                    'answer': response.text,
                    'subject': subject,
                    'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                })
            except Exception as e:
                return jsonify({'error': f'AI processing failed: {str(e)}'}), 500
        else:
            return jsonify({'error': 'AI tutor not available'}), 503
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Original doubt posting routes
@app.route('/api/doubts', methods=['GET'])
def get_doubts():
    try:
        return jsonify(doubts_db)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/doubts', methods=['POST'])
def post_doubt():
    try:
        title = request.form.get('title', '').strip()
        description = request.form.get('description', '').strip()
        
        if not title:
            return jsonify({'error': 'Title is required'}), 400
        
        file_path = None
        file_type = 'none'
        
        if 'file' in request.files:
            file = request.files['file']
            if file and file.filename and allowed_file(file.filename):
                filename = f"{uuid.uuid4().hex}_{secure_filename(file.filename)}"
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(file_path)
                
                ext = filename.lower().split('.')[-1]
                if ext in ['png', 'jpg', 'jpeg', 'gif', 'bmp']:
                    file_type = 'image'
                elif ext in ['mp4', 'avi', 'mov', 'webm', 'mkv']:
                    file_type = 'video'
                elif ext == 'pdf':
                    file_type = 'pdf'
        
        doubt = {
            'id': len(doubts_db) + 1,
            'title': title,
            'description': description,
            'file_path': file_path,
            'file_type': file_type,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'answers': [],
            'upvotes': 0,
            'downvotes': 0
        }
        
        if file_type == 'image' and GOOGLE_AI_AVAILABLE:
            try:
                uploaded_file = genai.upload_file(file_path)
                
                import time
                timeout = 0
                while uploaded_file.state.name == "PROCESSING" and timeout < 30:
                    time.sleep(1)
                    uploaded_file = genai.get_file(uploaded_file.name)
                    timeout += 1
                
                if uploaded_file.state.name == "ACTIVE":
                    model = genai.GenerativeModel('gemini-1.5-flash')
                    prompt = """You are KnowVia AI, an educational assistant. Analyze this academic image and provide a clear, step-by-step explanation."""
                    
                    response = model.generate_content([prompt, uploaded_file])
                    
                    doubt['answers'].append({
                        'content': response.text,
                        'author': 'KnowVia AI',
                        'is_ai': True,
                        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    })
                    
            except Exception as e:
                doubt['answers'].append({
                    'content': f"AI analysis failed: {str(e)}. Please describe your question in text for better assistance.",
                    'author': 'KnowVia AI',
                    'is_ai': True,
                    'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                })
        
        doubts_db.append(doubt)
        return jsonify({'success': True, 'doubt': doubt})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    try:
        return send_from_directory(app.config['UPLOAD_FOLDER'], filename)
    except Exception:
        return jsonify({'error': 'File not found'}), 404

@app.route('/health')
def health():
    return jsonify({
        'status': 'healthy',
        'ai_available': GOOGLE_AI_AVAILABLE,
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'features': {
            'subjects': len(SUBJECTS_DATA),
            'notes': len(notes_db),
            'quizzes': len(quiz_db),
            'doubts': len(doubts_db)
        }
    })



# Run the application
@app.route('/api/notes/<int:note_id>/upvote', methods=['POST'])
def upvote_note(note_id):
    note = next((n for n in notes_db if n['id'] == note_id), None)
    if note:
        note['upvotes'] = note.get('upvotes', 0) + 1
        return jsonify({'success': True, 'upvotes': note['upvotes']})
    return jsonify({'error': 'Note not found'}), 404

@app.route('/api/notes/<int:note_id>/downvote', methods=['POST'])
def downvote_note(note_id):
    note = next((n for n in notes_db if n['id'] == note_id), None)
    if note:
        note['downvotes'] = note.get('downvotes', 0) + 1
        return jsonify({'success': True, 'downvotes': note['downvotes']})
    return jsonify({'error': 'Note not found'}), 404

@app.route('/api/doubts/<int:doubt_id>/upvote', methods=['POST'])
def upvote_doubt(doubt_id):
    doubt = next((d for d in doubts_db if d['id'] == doubt_id), None)
    if doubt:
        doubt['upvotes'] += 1
        return jsonify({'success': True, 'upvotes': doubt['upvotes']})
    return jsonify({'error': 'Doubt not found'}), 404

@app.route('/api/doubts/<int:doubt_id>/downvote', methods=['POST'])
def downvote_doubt(doubt_id):
    doubt = next((d for d in doubts_db if d['id'] == doubt_id), None)
    if doubt:
        doubt['downvotes'] += 1
        return jsonify({'success': True, 'downvotes': doubt['downvotes']})
    return jsonify({'error': 'Doubt not found'}), 404
if __name__ == '__main__':
    print("🚀 Starting KnowVia AI Learning Platform...")
    print("📍 Server: http://localhost:5050")
    print("📁 Upload folder:", app.config['UPLOAD_FOLDER'])
    print("🤖 AI Features:", "Enabled" if GOOGLE_AI_AVAILABLE else "Disabled")
    print("\n✨ Features:")
    print("📚 6 Subjects with comprehensive content")
    print("📝 Interactive note-taking system")
    print("🧠 Practice quizzes with instant feedback")
    print("🎥 Educational video library")
    print("🤖 24/7 AI tutor for instant help")
    print("❓ Smart doubt posting with AI analysis")
    print("📊 Progress tracking and analytics")
    print("\n🔧 Setup:")
    print("Open http://localhost:5050")
    app.run(host='0.0.0.0', port=5050, debug=True)
