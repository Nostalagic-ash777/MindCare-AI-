from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, logout_user, login_required, UserMixin, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv
import os
import openai
from datetime import datetime
import re

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get("SECRET_KEY", "fallback-secret-key")
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///mindcare.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Please log in to access this page.'

# Set OpenAI API key
openai.api_key = os.environ.get("OPENAI_API_KEY")

# Database Models
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    chat_messages = db.relationship('ChatMessage', backref='user', lazy=True)
    journal_entries = db.relationship('JournalEntry', backref='user', lazy=True)
    mood_entries = db.relationship('MoodEntry', backref='user', lazy=True)

class ChatMessage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    message_text = db.Column(db.Text, nullable=False)
    is_user_message = db.Column(db.Boolean, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    is_crisis = db.Column(db.Boolean, default=False)

class JournalEntry(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    title = db.Column(db.String(200))
    content = db.Column(db.Text, nullable=False)
    mood_rating = db.Column(db.Integer)  # 1-10 scale
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class MoodEntry(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    mood_score = db.Column(db.Integer, nullable=False)  # 1-10 scale
    energy_level = db.Column(db.Integer)
    anxiety_level = db.Column(db.Integer)
    sleep_hours = db.Column(db.Float)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Crisis Detection Function
def detect_crisis(message):
    """Detect crisis keywords in user messages"""
    crisis_keywords = [
        'suicide', 'kill myself', 'end it all', 'hurt myself', 'self harm',
        'want to die', 'better off dead', 'no point living', 'hopeless',
        'cutting', 'pills', 'overdose', 'jump off', 'hanging', 'worthless',
        'everyone hates me', 'can\'t go on', 'tired of living'
    ]
    
    message_lower = message.lower()
    detected_keywords = []
    
    for keyword in crisis_keywords:
        if keyword in message_lower:
            detected_keywords.append(keyword)
    
    return len(detected_keywords) > 0, detected_keywords

# AI Response Generation
def generate_ai_response(user_message, user_context=None):
    """Generate AI response with safety checks"""
    
    # Crisis detection first
    is_crisis, crisis_keywords = detect_crisis(user_message)
    
    if is_crisis:
        crisis_response = (
            "I'm really concerned about what you've shared. Your feelings are valid, but I want to make sure you're safe. "
            "Please reach out to a trusted adult, counselor, or contact:\n\n"
            "🆘 National Suicide Prevention Lifeline: 988\n"
            "📱 Crisis Text Line: Text HOME to 741741\n"
            "🏥 Emergency: Call 911\n\n"
            "You don't have to go through this alone. There are people who want to help you."
        )
        return crisis_response, True
    
    # Generate AI response using OpenAI
    try:
        if openai.api_key:
            system_prompt = """You are MindCare AI, a compassionate mental health support chatbot designed specifically for teenagers and young adults.

Guidelines:
- Be empathetic, warm, and non-judgmental
- Use age-appropriate language for teens
- Provide emotional support and validation
- Suggest healthy coping strategies when appropriate
- Encourage professional help when needed
- Never provide medical diagnoses or prescribe medications
- Keep responses conversational and supportive (150-200 words max)
- Always remind that you're a supportive companion, not a replacement for professional care

Remember: You're here to listen, support, and guide teens toward appropriate resources."""

            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message}
                ],
                max_tokens=250,
                temperature=0.7
            )
            
            ai_message = response.choices[0].message.content.strip()
            
        else:
            # Fallback responses when OpenAI API is not available
            fallback_responses = {
                'anxiety': "I understand that anxiety can feel overwhelming. It's completely normal to feel this way sometimes. Have you tried any breathing exercises? Taking slow, deep breaths can help calm your mind. What's been triggering your anxiety lately?",
                'depression': "I'm sorry you're feeling this way. Depression can make everything feel heavy and difficult. Please know that these feelings are temporary, even though they don't feel like it right now. Have you been able to talk to anyone you trust about how you're feeling?",
                'stress': "It sounds like you're dealing with a lot of stress right now. That can be really exhausting. What's been the biggest source of stress for you lately? Sometimes breaking things down into smaller, manageable pieces can help.",
                'lonely': "Feeling lonely can be one of the hardest emotions to deal with. You're not alone in feeling this way - many teens experience loneliness. Is there anyone in your life you feel comfortable reaching out to?",
                'school': "School can definitely be stressful and overwhelming sometimes. It's important to remember that your grades don't define your worth as a person. What specific aspects of school are causing you the most stress?",
                'family': "Family relationships can be complicated, especially during the teenage years. It's normal to have conflicts or feel misunderstood sometimes. Would you like to talk about what's been happening with your family?",
                'default': "Thank you for sharing that with me. It takes courage to open up about your feelings. I'm here to listen and support you. How are you taking care of yourself today? What would help you feel a little better right now?"
            }
            
            # Simple keyword matching for fallback responses
            message_lower = user_message.lower()
            
            if any(word in message_lower for word in ['anxious', 'anxiety', 'panic', 'worried', 'nervous']):
                ai_message = fallback_responses['anxiety']
            elif any(word in message_lower for word in ['sad', 'depressed', 'down', 'empty', 'numb']):
                ai_message = fallback_responses['depression']
            elif any(word in message_lower for word in ['stress', 'stressed', 'overwhelmed', 'pressure']):
                ai_message = fallback_responses['stress']
            elif any(word in message_lower for word in ['lonely', 'alone', 'isolated', 'no friends']):
                ai_message = fallback_responses['lonely']
            elif any(word in message_lower for word in ['school', 'homework', 'grades', 'exam', 'test']):
                ai_message = fallback_responses['school']
            elif any(word in message_lower for word in ['family', 'parents', 'mom', 'dad', 'siblings']):
                ai_message = fallback_responses['family']
            else:
                ai_message = fallback_responses['default']
        
        return ai_message, False
        
    except Exception as e:
        print(f"Error generating AI response: {e}")
        return "I'm here to listen and support you. Sometimes technology has hiccups, but that doesn't change the fact that your feelings matter. What would you like to talk about?", False

# Routes
@app.route("/")
def index():
    """Landing page"""
    return render_template("index.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    """User registration"""
    if request.method == "POST":
        username = request.form.get("username")
        email = request.form.get("email")
        password = request.form.get("password")
        
        # Validation
        if not username or not email or not password:
            flash("All fields are required.", "error")
            return render_template("register.html")
        
        # Check if user already exists
        if User.query.filter_by(username=username).first():
            flash("Username already exists. Please choose a different one.", "error")
            return render_template("register.html")
        
        if User.query.filter_by(email=email).first():
            flash("Email already exists. Please use a different email.", "error")
            return render_template("register.html")
        
        # Create new user
        password_hash = generate_password_hash(password)
        user = User(username=username, email=email, password_hash=password_hash)
        
        db.session.add(user)
        db.session.commit()
        
        flash("Registration successful! Please log in.", "success")
        return redirect(url_for("login"))
    
    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    """User login"""
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        
        if not username or not password:
            flash("Please enter both username and password.", "error")
            return render_template("login.html")
        
        # Find user by username or email
        user = User.query.filter(
            (User.username == username) | (User.email == username)
        ).first()
        
        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            flash(f"Welcome back, {user.username}!", "success")
            return redirect(url_for("dashboard"))
        else:
            flash("Invalid username or password.", "error")
    
    return render_template("login.html")

@app.route("/logout")
@login_required
def logout():
    """User logout"""
    logout_user()
    flash("You have been logged out.", "info")
    return redirect(url_for("index"))

@app.route("/dashboard")
@login_required
def dashboard():
    """User dashboard"""
    # Get user statistics
    total_chats = ChatMessage.query.filter_by(user_id=current_user.id, is_user_message=True).count()
    total_journal_entries = JournalEntry.query.filter_by(user_id=current_user.id).count()
    recent_mood = MoodEntry.query.filter_by(user_id=current_user.id).order_by(MoodEntry.created_at.desc()).first()
    
    stats = {
        'total_chats': total_chats,
        'total_journal_entries': total_journal_entries,
        'recent_mood': recent_mood.mood_score if recent_mood else None,
        'days_active': (datetime.utcnow() - current_user.created_at).days + 1
    }
    
    return render_template("dashboard.html", stats=stats)

@app.route("/chat")
@login_required
def chat():
    """Chat interface"""
    # Get recent chat history
    messages = ChatMessage.query.filter_by(user_id=current_user.id)\
        .order_by(ChatMessage.timestamp.desc()).limit(20).all()
    messages.reverse()  # Show oldest first
    
    return render_template("chat.html", messages=messages)

@app.route("/send_message", methods=["POST"])
@login_required
def send_message():
    """Handle chat messages"""
    user_message = request.form.get("message", "").strip()
    
    if not user_message:
        flash("Please enter a message.", "error")
        return redirect(url_for("chat"))
    
    # Save user message
    user_chat = ChatMessage(
        user_id=current_user.id,
        message_text=user_message,
        is_user_message=True
    )
    db.session.add(user_chat)
    
    # Generate AI response
    ai_response, is_crisis = generate_ai_response(user_message)
    
    # Save AI response
    ai_chat = ChatMessage(
        user_id=current_user.id,
        message_text=ai_response,
        is_user_message=False,
        is_crisis=is_crisis
    )
    db.session.add(ai_chat)
    db.session.commit()
    
    if is_crisis:
        flash("Crisis resources have been provided. Please reach out for immediate help if needed.", "warning")
    
    return redirect(url_for("chat"))

@app.route("/journal")
@login_required
def journal():
    """Mood journal interface"""
    entries = JournalEntry.query.filter_by(user_id=current_user.id)\
        .order_by(JournalEntry.created_at.desc()).all()
    return render_template("journal.html", entries=entries)

@app.route("/add_journal_entry", methods=["POST"])
@login_required
def add_journal_entry():
    """Add journal entry"""
    title = request.form.get("title", "")
    content = request.form.get("content", "").strip()
    mood_rating = request.form.get("mood_rating", type=int)
    
    if not content:
        flash("Please write something in your journal entry.", "error")
        return redirect(url_for("journal"))
    
    entry = JournalEntry(
        user_id=current_user.id,
        title=title if title else f"Journal Entry - {datetime.now().strftime('%B %d, %Y')}",
        content=content,
        mood_rating=mood_rating
    )
    
    db.session.add(entry)
    db.session.commit()
    
    flash("Journal entry saved successfully!", "success")
    return redirect(url_for("journal"))

@app.route("/mood_tracking")
@login_required
def mood_tracking():
    """Mood tracking interface"""
    # Get recent mood entries for chart
    recent_moods = MoodEntry.query.filter_by(user_id=current_user.id)\
        .order_by(MoodEntry.created_at.desc()).limit(30).all()
    
    return render_template("mood_tracking.html", recent_moods=recent_moods)

@app.route("/add_mood_entry", methods=["POST"])
@login_required
def add_mood_entry():
    """Add mood tracking entry"""
    mood_score = request.form.get("mood_score", type=int)
    energy_level = request.form.get("energy_level", type=int)
    anxiety_level = request.form.get("anxiety_level", type=int)
    sleep_hours = request.form.get("sleep_hours", type=float)
    notes = request.form.get("notes", "")
    
    if not mood_score:
        flash("Please select your mood score.", "error")
        return redirect(url_for("mood_tracking"))
    
    # Check if user already has a mood entry for today
    today = datetime.now().date()
    existing_entry = MoodEntry.query.filter_by(user_id=current_user.id)\
        .filter(db.func.date(MoodEntry.created_at) == today).first()
    
    if existing_entry:
        # Update existing entry
        existing_entry.mood_score = mood_score
        existing_entry.energy_level = energy_level
        existing_entry.anxiety_level = anxiety_level
        existing_entry.sleep_hours = sleep_hours
        existing_entry.notes = notes
        flash("Today's mood entry updated!", "success")
    else:
        # Create new entry
        mood_entry = MoodEntry(
            user_id=current_user.id,
            mood_score=mood_score,
            energy_level=energy_level,
            anxiety_level=anxiety_level,
            sleep_hours=sleep_hours,
            notes=notes
        )
        db.session.add(mood_entry)
        flash("Mood entry saved successfully!", "success")
    
    db.session.commit()
    return redirect(url_for("mood_tracking"))

@app.route("/mindfulness")
@login_required
def mindfulness():
    """Mindfulness exercises interface"""
    return render_template("mindfulness.html")

@app.route("/resources")
@login_required
def resources():
    """Mental health resources"""
    return render_template("resources.html")

@app.route("/profile")
@login_required
def profile():
    """User profile"""
    return render_template("profile.html", user=current_user)

# Error handlers
@app.errorhandler(404)
def not_found_error(error):
    return render_template("404.html"), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template("500.html"), 500

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
        print("Database initialized successfully!")
    app.run(debug=True, host='0.0.0.0', port=5000)
