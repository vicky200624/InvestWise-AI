```markdown
# InvestWise AI

InvestWise AI is a modern, full-stack fintech web application built with Django that aggregates, tracks, and analyzes retail investment portfolios across multiple asset classes (Equity Stocks, Mutual Funds, Gold/SGBs, and REITs). It features live broker integration (Angel One SmartAPI), real-time market fallback feeds (Yahoo Finance), a dynamic portfolio health analyzer, and an integrated generative AI advisory system powered by Google's Gemini SDK.

---

## Key Features

* **Multi-Broker Integration:** Securely connect and authenticate with broker APIs like Angel One (with automated TOTP generation) to pull live Demat holdings and real-time Net Worth tracking.
* **Unified Asset Dashboard:** Clean cockpit view displaying Equity Stocks, Mutual Funds, Gold, and REIT allocations with computed real-time Profit & Loss (P&L) metrics.
* **Dynamic Health Scoring:** Automatically computes a portfolio health score based on asset diversification and performance metrics.
* **AI Financial Advisor:** An embedded interactive advisor utilizing the Google GenAI SDK (`gemini-1.5-flash`) to provide smart, SEBI-compliant guidance.
* **Text-to-Speech (TTS) Integration:** Integrated audio output for AI advisory tips via ElevenLabs.
* **Print-Ready User Manual:** Built-in PDF export guide detailing how users can generate and link their third-party broker API keys safely.

---

## Tech Stack

* **Backend:** Python, Django
* **Database:** SQLite / MySQL (Django ORM)
* **APIs & SDKs:** Angel One SmartAPI, Google GenAI SDK (`google-genai`), ElevenLabs API, Yahoo Finance (`yfinance`)
* **Frontend:** Tailwind CSS, HTML5, Vanilla JavaScript

---

## Project Structure

```text
investai/
├── investwise_core/       # Main Django project settings & URL routing
├── investwise/            # Core app module
│   ├── migrations/        # Database migrations
│   ├── templates/         # HTML templates (Dashboard, Connect Broker, Manual, etc.)
│   ├── models.py          # Database models (BrokerCredentials)
│   ├── views.py           # Application views, broker routing, and AI endpoints
│   └── urls.py            # App-level routing rules
├── manage.py              # Django project management script
└── requirements.txt       # Python package dependencies

```

---

## Setup & Installation

### 1. Clone and Navigate to the Repository

```bash
git clone <repository-url>
cd investai

```

### 2. Create and Activate a Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate

```

### 3. Install Dependencies

Ensure you have all required packages installed in your environment:

```bash
pip install django smartapi-python pyotp yfinance requests google-genai websocket-client

```

### 4. Configure Environment Variables

Set up your required environment keys in your local environment or terminal session:

```bash
export GEMINI_API_KEY="your_google_genai_api_key"
export ELEVENLABS_API_KEY="your_elevenlabs_api_key"

```

### 5. Apply Database Migrations

```bash
python manage.py makemigrations
python manage.py migrate

```

### 6. Run the Development Server

```bash
python manage.py runserver

```

Open your browser and navigate to `http://127.0.0.1:8000/`.

```

```
