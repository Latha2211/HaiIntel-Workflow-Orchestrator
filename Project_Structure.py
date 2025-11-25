# 📁 Project Structure

Complete file organization for HaiIntel Workflow Orchestrator

## 🌳 Directory Tree

```
haiintel-workflow-orchestrator/
│
├── 📄 main.py                          # Main application entry point
├── 📄 README.md                        # Project documentation
├── 📄 SETUP_GUIDE.md                   # Quick start guide
├── 📄 PROJECT_STRUCTURE.md             # This file
├── 📄 LICENSE                          # MIT License
├── 📄 requirements.txt                 # Python dependencies
├── 📄 .env.example                     # Environment variables template
├── 📄 .env                            # Your environment (DO NOT COMMIT)
├── 📄 .gitignore                      # Git ignore rules
├── 📄 Dockerfile                      # Docker configuration
├── 📄 docker-compose.yml              # Docker Compose setup
├── 📄 Makefile                        # Development commands
├── 📄 HaiIntel.postman_collection.json # Postman API collection
│
├── 📁 config/                          # Configuration module
│   ├── __init__.py                    # Package initialization
│   └── settings.py                    # Application settings
│
├── 📁 services/                        # Business logic services
│   ├── __init__.py                    # Package initialization
│   ├── llm_service.py                 # AI classification service
│   ├── ticket_service.py              # Ticket management
│   ├── notification_service.py        # Multi-channel notifications
│   ├── analytics_service.py           # Analytics and reporting
│   └── slack_service.py               # Slack integration
│
├── 📁 utils/                           # Utility functions
│   ├── __init__.py                    # Package initialization
│   ├── logger.py                      # Advanced logging system
│   └── helpers.py                     # Helper functions
│
├── 📁 tests/                           # Test suite
│   ├── __init__.py                    # Package initialization
│   ├── test_workflow.py               # Integration tests
│   ├── test_llm_service.py           # LLM service tests
│   └── test_ticket_service.py        # Ticket service tests
│
├── 📁 logs/                            # Application logs (auto-generated)
│   └── haiintel.log                   # Main log file
│
├── 📁 data/                            # Data storage (auto-generated)
│   └── analytics.db                   # SQLite analytics database
│
└── 📁 docs/                            # Additional documentation (optional)
    ├── API.md                         # API documentation
    ├── ARCHITECTURE.md                # System architecture
    └── DEPLOYMENT.md                  # Deployment guide
```

## 📝 File Descriptions

### Root Level Files

| File | Purpose | Required |
|------|---------|----------|
| `main.py` | FastAPI application entry point | ✅ Yes |
| `README.md` | Project overview and documentation | ✅ Yes |
| `SETUP_GUIDE.md` | Quick start installation guide | ✅ Yes |
| `requirements.txt` | Python package dependencies | ✅ Yes |
| `.env.example` | Environment variables template | ✅ Yes |
| `.env` | Your configuration (git-ignored) | ✅ Yes |
| `.gitignore` | Git ignore patterns | ✅ Yes |
| `LICENSE` | MIT License | ✅ Yes |
| `Dockerfile` | Docker image definition | ⚪ Optional |
| `docker-compose.yml` | Multi-container orchestration | ⚪ Optional |
| `Makefile` | Development shortcuts | ⚪ Optional |
| `HaiIntel.postman_collection.json` | API testing collection | ⚪ Optional |

### Config Module (`config/`)

```
config/
├── __init__.py       # Exports settings
└── settings.py       # Pydantic settings management
```

**Purpose:** Centralized configuration using environment variables and pydantic-settings.

**Key Features:**
- Environment variable loading
- Type validation
- Default values
- Separate dev/prod configs

### Services Module (`services/`)

```
services/
├── __init__.py                 # Exports all services
├── llm_service.py             # AI-powered classification
├── ticket_service.py          # Ticket CRUD operations
├── notification_service.py    # Email/SMS/WhatsApp
├── analytics_service.py       # Database & reporting
└── slack_service.py           # Team notifications
```

**Service Responsibilities:**

#### `llm_service.py`
- OpenAI/Anthropic integration
- Issue classification
- Sentiment analysis
- Urgency detection
- Fallback to rule-based

#### `ticket_service.py`
- Ticket creation (reqres.in API)
- Status tracking
- Local caching
- Graceful degradation

#### `notification_service.py`
- Email via SMTP
- SMS via Twilio
- WhatsApp via Twilio
- Multi-channel orchestration
- Retry logic

#### `analytics_service.py`
- SQLite database
- Issue tracking
- Dashboard generation
- Export functionality

#### `slack_service.py`
- Webhook integration
- Formatted alerts
- Color-coded messages
- Field attachments

### Utils Module (`utils/`)

```
utils/
├── __init__.py      # Exports utilities
├── logger.py        # Logging configuration
└── helpers.py       # Helper functions
```

**Utilities:**

#### `logger.py`
- Colored console output
- File rotation
- Multiple log levels
- Custom formatters

#### `helpers.py`
- Ticket ID generation
- Priority calculation
- Retry decorators
- Performance timing
- Data sanitization

### Tests Module (`tests/`)

```
tests/
├── __init__.py           # Package marker
├── test_workflow.py      # E2E workflow tests
├── test_llm_service.py  # LLM unit tests
└── test_ticket_service.py # Ticket unit tests
```

**Testing Strategy:**
- Integration tests for workflows
- Unit tests for services
- Pytest with async support
- Coverage reporting

### Auto-Generated Directories

#### `logs/`
- Created automatically
- Contains rotated log files
- Max 10MB per file
- 5 backup files kept

#### `data/`
- Created automatically
- SQLite database
- Analytics storage
- Auto-initialized schema

## 🔨 Creating the Project Structure

### Manual Setup

```bash
# Create main directories
mkdir -p config services utils tests logs data docs

# Create __init__.py files
touch config/__init__.py
touch services/__init__.py
touch utils/__init__.py
touch tests/__init__.py

# Create main files
touch main.py
touch README.md
touch SETUP_GUIDE.md
touch requirements.txt
touch .env.example
touch .gitignore

# Create config files
touch config/settings.py

# Create service files
touch services/llm_service.py
touch services/ticket_service.py
touch services/notification_service.py
touch services/analytics_service.py
touch services/slack_service.py

# Create utility files
touch utils/logger.py
touch utils/helpers.py

# Create test files
touch tests/test_workflow.py
```

### Using Script

Create `setup.sh`:
```bash
#!/bin/bash
echo "🔧 Setting up project structure..."

# Create directories
mkdir -p config services utils tests logs data docs

# Create __init__ files
echo '"""Configuration module"""' > config/__init__.py
echo '"""Services module"""' > services/__init__.py
echo '"""Utilities module"""' > utils/__init__.py
echo '"""Tests module"""' > tests/__init__.py

# Copy environment template
cp .env.example .env

echo "✅ Project structure created!"
echo "⚠️  Don't forget to:"
echo "   1. Edit .env with your credentials"
echo "   2. Run: pip install -r requirements.txt"
echo "   3. Run: python main.py"
```

Run it:
```bash
chmod +x setup.sh
./setup.sh
```

## 📊 File Size Reference

Typical file sizes after setup:

| File/Directory | Size | Notes |
|----------------|------|-------|
| `main.py` | ~15 KB | Core application |
| `services/*.py` | ~5-8 KB each | Business logic |
| `utils/*.py` | ~3-5 KB each | Helpers |
| `logs/haiintel.log` | Grows | Max 10MB + 5 backups |
| `data/analytics.db` | Grows | Depends on usage |
| `requirements.txt` | ~500 bytes | Dependencies list |
| `.env` | ~2 KB | Configuration |

**Total:** ~100 KB (excluding logs and data)

## 🎯 Best Practices

### 1. Module Organization
- One service per file
- Clear separation of concerns
- Reusable utilities
- Comprehensive tests

### 2. Naming Conventions
- `snake_case` for files and functions
- `PascalCase` for classes
- `UPPER_CASE` for constants
- Descriptive, not cryptic names

### 3. Import Structure
```python
# Standard library
import os
from datetime import datetime

# Third-party
from fastapi import FastAPI
import aiohttp

# Local imports
from config.settings import settings
from services.llm_service import LLMService
from utils.logger import setup_logger
```

### 4. Documentation
- Docstrings for all public functions
- Type hints everywhere
- README for each module
- Inline comments for complex logic

## 🔍 Finding Files

### By Functionality

**Need to modify classifications?**
→ `services/llm_service.py`

**Change notification templates?**
→ `services/notification_service.py`

**Adjust logging?**
→ `utils/logger.py`

**Update configuration?**
→ `config/settings.py` and `.env`

**Add new endpoints?**
→ `main.py`

**Fix tests?**
→ `tests/test_*.py`

### By Feature

| Feature | Primary Files |
|---------|--------------|
| AI Classification | `services/llm_service.py` |
| Ticket Management | `services/ticket_service.py` |
| Email/SMS/WhatsApp | `services/notification_service.py` |
| Slack Alerts | `services/slack_service.py` |
| Analytics | `services/analytics_service.py` |
| Logging | `utils/logger.py` |
| API Endpoints | `main.py` |
| Configuration | `config/settings.py`, `.env` |
| Testing | `tests/test_*.py` |

## 📦 Dependencies Map

```
main.py
├── config.settings
├── services.llm_service
│   ├── config.settings
│   └── utils.logger
├── services.ticket_service
│   ├── config.settings
│   └── utils.logger
├── services.notification_service
│   ├── config.settings
│   └── utils.logger
├── services.analytics_service
│   ├── config.settings
│   └── utils.logger
├── services.slack_service
│   ├── config.settings
│   └── utils.logger
└── utils.helpers
    └── utils.logger
```

## 🚀 Ready to Start!

You now have a complete understanding of the project structure. Ready to:

1. ✅ Clone/create the structure
2. ✅ Install dependencies
3. ✅ Configure environment
4. ✅ Run the application
5. ✅ Start customizing!

For setup instructions, see [SETUP_GUIDE.md](SETUP_GUIDE.md)

---

**Questions?** Open an issue or check the [README](README.md)
