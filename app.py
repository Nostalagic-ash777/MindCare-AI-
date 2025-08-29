from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, logout_user, login_required, UserMixin, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv
import os
from openai import OpenAI
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

# Initialize Hugging Face OpenAI-compatible client
client = OpenAI(
    base_url="https://router.huggingface.co/v1",
    api_key=os.environ.get("HF_TOKEN")
)

# Database Models
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

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

def detect_crisis(message):
    crisis_keywords = [
        'suicide', 'kill myself', 'end it all', 'hurt myself', 'self harm',
        'want to die', 'better off dead', 'no point living', 'hopeless',
        'cutting', 'pills', 'overdose', 'jump off', 'hanging', 'worthless',
        'everyone hates me', "can't go on", 'tired of living'
    ]
    message_lower = message.lower()
    detected_keywords = [kw for kw in crisis_keywords if kw in message_lower]
    return len(detected_keywords) > 0, detected_keywords

def get_chat_response(user_message):
    try:
        response = client.chat.completions.create(
            model="openai/gpt-oss-20b:together",
            messages=[{"role": "user", "content": user_message}],
            max_tokens=250,
            temperature=0.7
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"Error calling chat API: {e}")
        return "I'm here to listen and support you. Sometimes technology has hiccups, but your feelings matter."

def generate_ai_response(user_message, user_context=None):
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

    try:
        ai_message = get_chat_response(user_message)
        return ai_message, False

    except Exception as e:
        print(f"Error generating AI response: {e}")
        fallback_responses = {
            'anxiety': "I understand that anxiety can feel overwhelming. It's completely normal to feel this way sometimes. Have you tried any breathing exercises? Taking slow, deep breaths can help calm your mind. What's been triggering your anxiety lately?",
            'depression': "I'm sorry you're feeling this way. Depression can make everything feel heavy and difficult. Please know that these feelings are temporary, even though they don't feel like it right now. Have you been able to talk to anyone you trust about how you're feeling?",
            'stress': "It sounds like you're dealing with a lot of stress right now. That can be really exhausting. What's been the biggest source of stress for you lately? Sometimes breaking things down into smaller, manageable pieces can help.",
            'lonely': "Feeling lonely can be one of the hardest emotions to deal with. You're not alone in feeling this way - many teens experience loneliness. Is there anyone in your life you feel comfortable reaching out to?",
            'school': "School can definitely be stressful and overwhelming sometimes. It's important to remember that your grades don't define your worth as a person. What specific aspects of school are causing you the most stress?",
            'family': "Family relationships can be complicated, especially during the teenage years. It's normal to have conflicts or feel misunderstood sometimes. Would you like to talk about what's been happening with your family?"
        }
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
            try:
                ai_message = get_chat_response(user_message)
            except Exception as e2:
                print(f"Error generating fallback AI response: {e2}")
                ai_message = "Thank you for sharing that with me. It takes courage to open up about your feelings. I'm here to listen and support you. How are you taking care of yourself today? What would help you feel a little better right now?"
        return ai_message, False

# ... [All your route and app logic as before, unchanged] ...

# Example Chat message route demonstrating chat usage
@app.route("/send_message", methods=["POST"])
@login_required
def send_message():
    user_message = request.form.get("message", "").strip()
    if not user_message:
        flash("Please enter a message.", "error")
        return redirect(url_for("chat"))

    user_chat = ChatMessage(
        user_id=current_user.id,
        message_text=user_message,
        is_user_message=True
    )
    db.session.add(user_chat)

    ai_response, is_crisis = generate_ai_response(user_message)

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

# Continue with your other routes and error handlers as before...

with app.app_context():
    db.create_all()

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
        print("Database initialized successfully!")
    app.run(debug=True, host='0.0.0.0', port=5000)

@app.route('/healthz')
def healthz():
    return 'OK!', 200
