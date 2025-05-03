# Email Assistant

A smart email assistant that helps prioritize and manage your email inbox using IMAP and AI.

## Features

- 📧 Universal email support via IMAP protocol
- 🤖 AI-powered email analysis and prioritization using Gemini
- ⚡ Automatic email classification and organization
- 🔔 Desktop notifications for important emails
- 🎯 Smart email actions (archive, label, etc.)


```
email-assistant/
├── app/
│   ├── main.py           # FastAPI application
│   ├── core/
│   │   ├── config.py     # Configuration settings
│   │   └── security.py   # Security utilities
│   ├── services/
│   │   ├── email.py      # IMAP email service
│   │   ├── ai.py         # Gemini AI service
│   │   └── notify.py     # Notification service
│   └── api/
│       └── v1/           # API endpoints
├── tests/                # Test files
├── requirements.txt      # Project dependencies
└── .env                 # Environment variables
```