# MindCare AI - Mental Health Chatbot

A comprehensive AI-powered mental health support application designed specifically for teenagers and young adults. MindCare AI provides empathetic conversations, mood journaling, tracking, and crisis support in a safe, confidential environment.

## 🌟 Features

- **AI Chat Support**: Empathetic conversations with OpenAI-powered responses
- **User Authentication**: Secure login and registration system
- **Mood Journaling**: Daily journaling with mood rating and tracking
- **Mood Tracking**: Visual tracking of emotional wellbeing over time
- **Crisis Detection**: Automatic identification of concerning messages with immediate resource recommendations
- **Mindfulness Exercises**: Guided meditation and breathing techniques
- **Professional Resources**: 24/7 access to crisis hotlines and mental health resources
- **Privacy & Security**: Confidential conversations with secure data handling



## 📁 Project Structure

```
mindcare-ai/
├── Backend/
|   ├── app.py                 # Main Flask application
|   ├── requirements.txt       # Python dependencies
|   ├── .env                  # Environment variables (not in repo)
├── templates/            # HTML templates
│   ├── index.html        # Landing page
│   ├── register.html     # Registration page
│   ├── login.html        # Login page
│   ├── dashboard.html    # User dashboard
│   └── chat.html         # Chat interface
├── static/
│   └── style.css         # CSS styles
└── mindcare.db           # SQLite database (auto-generated)
```



### Database
The application uses SQLite for simplicity. The database will be automatically created when you first run the application.

## 🎯 Core Features

### AI Chat System
- Powered by OpenAI's GPT-3.5 Turbo
- Empathetic responses tailored for mental health support
- Crisis detection with automatic resource recommendations
- Fallback responses when API is unavailable

### Safety Features
- **Crisis Detection**: Automatic identification of concerning keywords
- **Professional Resources**: Immediate access to crisis hotlines
- **Privacy Protection**: Secure data handling and confidential conversations
- **Professional Disclaimers**: Clear messaging about limitations

### User Management
- Secure authentication with password hashing
- Personal dashboard with usage statistics
- Individual chat history and mood tracking
- Profile management

## 🛡️ Safety & Privacy

### Crisis Support
The application includes comprehensive crisis detection:
- Keyword-based identification of concerning messages
- Immediate display of crisis resources and hotlines
- Professional disclaimer messaging
- Encouragement to seek professional help

### Privacy Protection
- All conversations are confidential
- Secure password hashing
- Local database storage
- No sharing of personal information

## 🔗 Crisis Resources

The application provides immediate access to:
- **National Suicide Prevention Lifeline**: 988
- **Crisis Text Line**: Text HOME to 741741
- **Emergency Services**: 911

## 🚀 Deployment

### Local Development
```bash
python app.py
```
The application will run at `http://localhost:5000`

### Production Deployment
1. Set `FLASK_ENV=production` in your environment
2. Use a production WSGI server like Gunicorn
3. Configure proper SSL/HTTPS
4. Set up proper database backup and monitoring

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## ⚖️ Ethical Considerations

This application is designed to:
- Provide supportive companionship, not replace professional therapy
- Encourage users to seek professional help when appropriate
- Maintain strict confidentiality and privacy
- Provide immediate crisis resources when needed

**Important**: This application is not a substitute for professional mental health care. Users experiencing mental health crises should contact emergency services or professional mental health providers immediately.

## 📜 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- OpenAI for providing the GPT API
- Flask community for the excellent web framework
- Mental health professionals who inform best practices
- The open-source community for various libraries and tools

## 📞 Support

If you're experiencing a mental health crisis:
- **Call 988** (National Suicide Prevention Lifeline)
- **Text HOME to 741741** (Crisis Text Line)
- **Call 911** for emergency services
- Contact your local mental health professional

For technical support or questions about this application, please open an issue on GitHub.

---

**Disclaimer**: MindCare AI is designed to provide supportive conversations and mental health resources. It is not intended to replace professional mental health services, diagnosis, or treatment. If you are experiencing a mental health emergency, please contact emergency services or a mental health professional immediately.
