# 🚀 HaiIntel Workflow Orchestrator

![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.109.0-green.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)

An AI-powered multi-channel customer support automation system that orchestrates cross-channel issue resolutions with intelligent classification, sentiment analysis, and comprehensive analytics.

## ✨ Features

- 🤖 **AI-Powered Classification**: Automatic issue categorization using OpenAI/Anthropic
- 📊 **Sentiment Analysis**: Real-time customer sentiment detection
- 📧 **Multi-Channel Support**: Email, SMS, and WhatsApp notifications
- 🎫 **Ticket Management**: Automated ticket creation and tracking
- ⏰ **Smart Reminders**: 24-hour follow-up for unresolved issues
- 💬 **Slack Integration**: Team notifications for critical issues
- 📈 **Analytics Dashboard**: Comprehensive reporting and insights
- 🔄 **Error Handling**: Robust retry mechanisms and graceful degradation
- 📝 **Advanced Logging**: Colored console logs with file rotation

## 🏗️ Architecture

```
┌─────────────┐
│   Webhook   │
│  (FastAPI)  │
└──────┬──────┘
       │
       ├──► 🤖 LLM Service (OpenAI/Anthropic)
       │     └─► Category, Sentiment, Urgency
       │
       ├──► 🎫 Ticket Service (reqres.in API)
       │     └─► Create & Track Tickets
       │
       ├──► 📢 Notification Service
       │     ├─► Email (SMTP)
       │     ├─► SMS (Twilio)
       │     └─► WhatsApp (Twilio)
       │
       ├──► 💬 Slack Service
       │     └─► Team Alerts
       │
       ├──► 📊 Analytics Service
       │     └─► SQLite Database
       │
       └──► ⏰ Background Tasks
             └─► 24h Reminders
```

## 📦 Installation

### Prerequisites

- Python 3.9 or higher
- pip package manager
- (Optional) Virtual environment

### Setup Steps

1. **Clone the repository**
```bash
git clone https://github.com/yourusername/haiintel-workflow-orchestrator.git
cd haiintel-workflow-orchestrator
```

2. **Create virtual environment**
```bash
python -m venv venv

# On Windows
venv\Scripts\activate

# On macOS/Linux
source venv/bin/activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Configure environment variables**
```bash
cp .env.example .env
# Edit .env with your API keys and configuration
```

5. **Create required directories**
```bash
mkdir -p logs data
```

## ⚙️ Configuration

### Required Configuration

Edit the `.env` file with your credentials:

```bash
# Choose your LLM provider
LLM_PROVIDER=openai  # or anthropic
OPENAI_API_KEY=sk-...

# Email configuration
SMTP_USERNAME=your_email@gmail.com
SMTP_PASSWORD=your_app_password

# Twilio for SMS/WhatsApp
TWILIO_ACCOUNT_SID=AC...
TWILIO_AUTH_TOKEN=...
TWILIO_PHONE_NUMBER=+1234567890

# Slack webhook
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/...
```

### Optional Configuration

- `REMINDER_DELAY_SECONDS`: Time before sending reminder (default: 86400 = 24h)
- `MAX_RETRIES`: Number of retry attempts (default: 3)
- `LOG_LEVEL`: Logging level (DEBUG, INFO, WARNING, ERROR)

## 🚀 Usage

### Start the Server

```bash
# Development mode (with auto-reload)
python main.py

# Or using uvicorn directly
uvicorn main:app --reload --port 8000
```

### API Endpoints

#### 1. Health Check
```bash
GET http://localhost:8000/health
```

#### 2. Submit Customer Issue
```bash
POST http://localhost:8000/webhook/customer-issue
Content-Type: application/json

{
  "customerId": "99876",
  "channel": "whatsapp",
  "message": "My credit card payment was deducted twice yesterday."
}
```

**Response:**
```json
{
  "success": true,
  "ticket_id": "TKT-20231215-ABC123",
  "category": "duplicate_payment",
  "sentiment": "negative",
  "priority": "high",
  "channels_notified": ["whatsapp", "email"],
  "estimated_resolution": "2023-12-15T14:30:00",
  "message": "Issue processed successfully. Ticket TKT-20231215-ABC123 created."
}
```

#### 3. Get Analytics Dashboard
```bash
GET http://localhost:8000/analytics/dashboard
```

#### 4. Get Ticket Status
```bash
GET http://localhost:8000/tickets/{ticket_id}
```

### Example cURL Commands

```bash
# Submit issue
curl -X POST http://localhost:8000/webhook/customer-issue \
  -H "Content-Type: application/json" \
  -d '{
    "customerId": "99876",
    "channel": "email",
    "message": "I cannot log into my account"
  }'

# Get analytics
curl http://localhost:8000/analytics/dashboard

# Health check
curl http://localhost:8000/health
```

## 🔄 Workflow

When a customer issue is received, the system:

1. **Receives** the message via webhook
2. **Classifies** using AI (category, sentiment, urgency)
3. **Creates** a ticket in the external system
4. **Sends** acknowledgments via multiple channels
5. **Notifies** the team via Slack
6. **Schedules** a 24-hour reminder
7. **Tracks** analytics for reporting

## 📊 Issue Categories

- `duplicate_payment` - Payment charged multiple times
- `refund_request` - Customer requesting refund
- `account_access` - Login or access issues
- `technical_issue` - System errors or bugs
- `billing_inquiry` - Questions about charges
- `general_inquiry` - General questions
- `complaint` - Customer complaints
- `feature_request` - Feature suggestions

## 🎯 Priority Calculation

Priority is automatically calculated based on:
- **Sentiment**: Very negative → Higher priority
- **Urgency**: Critical/High → Higher priority
- **Category**: Payment/Access issues → Higher priority

**Priority Levels:**
- `high` - Response within 2 hours
- `medium` - Response within 12 hours
- `low` - Response within 24 hours

## 📈 Analytics

The system tracks:
- Total issues by category
- Sentiment distribution
- Channel preferences
- Average resolution time
- Resolution rate
- Daily trends

Access the analytics dashboard:
```bash
GET http://localhost:8000/analytics/dashboard
```

## 🧪 Testing

### Run Tests
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=. --cov-report=html

# Run specific test file
pytest tests/test_llm_service.py -v
```

### Manual Testing

Use the provided test data:
```bash
python tests/test_workflow.py
```

## 📁 Project Structure

```
haiintel-workflow-orchestrator/
├── main.py                      # Main application
├── config/
│   ├── __init__.py
│   └── settings.py              # Configuration management
├── services/
│   ├── __init__.py
│   ├── llm_service.py           # AI classification
│   ├── ticket_service.py        # Ticket management
│   ├── notification_service.py  # Multi-channel notifications
│   ├── analytics_service.py     # Analytics & reporting
│   └── slack_service.py         # Slack integration
├── utils/
│   ├── __init__.py
│   ├── logger.py                # Advanced logging
│   └── helpers.py               # Utility functions
├── tests/
│   ├── __init__.py
│   ├── test_llm_service.py
│   ├── test_ticket_service.py
│   └── test_workflow.py
├── logs/                        # Log files (auto-created)
├── data/                        # Analytics database (auto-created)
├── .env.example                 # Environment template
├── .gitignore
├── requirements.txt
├── README.md
└── LICENSE
```

## 🔒 Security

- API keys stored in environment variables
- No sensitive data in logs
- Customer IDs can be hashed
- Optional API key authentication

## 🐛 Troubleshooting

### Common Issues

**1. LLM API Errors**
- Verify API keys in `.env`
- Check API quotas/limits
- System falls back to rule-based classification

**2. Notification Failures**
- Verify SMTP/Twilio credentials
- Check network connectivity
- System continues workflow even if notifications fail

**3. Database Errors**
- Ensure `data/` directory exists
- Check file permissions
- Database auto-initializes on startup

### Debug Mode

Enable debug logging:
```bash
# In .env
LOG_LEVEL=DEBUG
DEBUG=true
```

## 🤝 Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Add tests for new features
4. Ensure all tests pass
5. Submit a pull request

### Code Style

```bash
# Format code
black .

# Sort imports
isort .

# Lint code
flake8 .
```

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- FastAPI for the excellent web framework
- OpenAI/Anthropic for LLM capabilities
- Twilio for SMS/WhatsApp integration
- The open-source community

## 📧 Support

For issues and questions:
- 📫 Email: latharaja4321@gmail.com
  

## 🗺️ Roadmap

- [ ] Add more LLM providers
- [ ] Implement real-time WebSocket notifications
- [ ] Add custom workflow builder
- [ ] Create web dashboard UI
- [ ] Add multi-language support
- [ ] Implement ML-based priority prediction
- [ ] Add integration with more ticket systems

---


