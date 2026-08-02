# InvestWise AI 3.0

![Production Ready](https://img.shields.io/badge/status-production%20ready-green)
![Python](https://img.shields.io/badge/python-3.11-blue)
![Django](https://img.shields.io/badge/django-5.0-green)
![React](https://img.shields.io/badge/react-18.2-cyan)
![Docker](https://img.shields.io/badge/docker-ready-blue)

**InvestWise AI 3.0** is a production-ready, AI-powered investment analysis platform that combines autonomous multi-agent analysis, portfolio optimization, and real-time market intelligence.

## Features

### Core Capabilities
- **Autonomous AI Analysis**: Multi-agent LangGraph workflow with Gemini 2.5 Flash integration
- **Portfolio Management**: Real-time tracking, broker sync (Angel One, Zerodha), and optimization
- **Research Engine**: Fundamental, quantitative, and sentiment analysis with XAI (SHAP values)
- **RAG Pipeline**: SEC EDGAR filing ingestion with ChromaDB vector store
- **Predictive Models**: LSTM, GRU, FNN, and XGBoost ensemble predictions
- **News Sentiment**: FinBERT-powered sentiment analysis with Finnhub integration
- **Watchlists & Alerts**: Real-time price alerts and watchlist management
- **Chat Assistant**: Context-aware AI chat with conversation memory

### Technical Features
- **Security**: JWT authentication, API versioning, rate limiting, CORS, security headers
- **Performance**: Redis caching, Celery async tasks, database query optimization
- **Monitoring**: Request logging, error tracking, health checks
- **Testing**: Comprehensive test suite with 80%+ coverage
- **Deployment**: Docker, Docker Compose, Nginx, Gunicorn, PostgreSQL, Redis

## Architecture

```
InvestWise AI 3.0
├── Backend (Django 5.0 + DRF)
│   ├── REST API with JWT authentication
│   ├── Celery async task queue
│   ├── Redis caching layer
│   └── PostgreSQL database
├── AI Engine (Python)
│   ├── LangChain/LangGraph orchestration
│   ├── Gemini 2.5 Flash LLM
│   ├── RAG pipeline (ChromaDB)
│   └── ML models (LSTM, GRU, FNN, XGBoost)
└── Frontend (React 18 + TypeScript)
    ├── Vite build system
    ├── Tailwind CSS styling
    ├── Framer Motion animations
    └── Real-time updates
```

## Quick Start

### Prerequisites
- Docker & Docker Compose
- Python 3.11+
- Node.js 20+
- PostgreSQL 15+ (optional, SQLite works for development)
- Redis 7+ (optional, LocMem cache works for development)

### Installation

1. **Clone the repository**
```bash
git clone https://github.com/vicky200624/InvestWise-AI.git
cd InvestWise-AI
```

2. **Set up environment variables**
```bash
cp .env.example .env
# Edit .env with your API keys and configuration
```

3. **Start with Docker Compose**
```bash
docker-compose up -d
```

4. **Run migrations**
```bash
docker-compose exec backend python manage.py migrate
```

5. **Create superuser**
```bash
docker-compose exec backend python manage.py createsuperuser
```

6. **Access the application**
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000/api/v1/
- Admin: http://localhost:8000/admin/

## Development Setup

### Backend

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run migrations
python manage.py makemigrations
python manage.py migrate

# Start development server
python manage.py runserver
```

### Frontend

```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

### Celery Worker (for async tasks)

```bash
# In a separate terminal
celery -A config worker --loglevel=info
```

### Celery Beat (for scheduled tasks)

```bash
# In a separate terminal
celery -A config beat --loglevel=info
```

## Environment Variables

See `.env.example` for all available configuration options.

### Required API Keys
- `GEMINI_API_KEY` - Google Gemini AI
- `FMP_API_KEY` - Financial Modeling Prep
- `FINNHUB_API_KEY` - Finnhub News & Sentiment
- `FRED_API_KEY` - Federal Reserve Economic Data

### Optional API Keys
- `SEC_API_KEY` - SEC EDGAR filings
- `ELEVENLABS_API_KEY` - Voice synthesis
- `DEEPGRAM_API_KEY` - Speech-to-text

## API Documentation

### Authentication
All API endpoints require JWT authentication except `/api/v1/auth/` endpoints.

```bash
# Login
POST /api/v1/auth/login/
{
  "username": "user",
  "password": "password"
}

# Response
{
  "access": "eyJ...",
  "refresh": "eyJ..."
}
```

### Key Endpoints

#### Portfolio
- `GET /api/v1/portfolio/holdings/` - List holdings
- `POST /api/v1/portfolio/holdings/` - Add holding
- `GET /api/v1/portfolio/dashboard/` - Dashboard summary
- `POST /api/v1/portfolio/sync-broker/` - Sync broker holdings

#### Research
- `POST /api/v1/research/analyze/` - Run stock analysis
- `GET /api/v1/research/history/` - Analysis history
- `POST /api/v1/research/feedback/` - Submit feedback

#### Watchlist
- `GET /api/v1/watchlist/watchlists/` - List watchlists
- `POST /api/v1/watchlist/items/` - Add to watchlist
- `POST /api/v1/watchlist/alerts/` - Create price alert

#### Chat
- `GET /api/v1/chat/sessions/` - List chat sessions
- `POST /api/v1/chat/message/` - Send message

## Testing

### Backend Tests
```bash
python manage.py test
```

### Frontend Tests
```bash
cd frontend
npm test
```

### Integration Tests
```bash
# Run all tests
pytest tests/ -v
```

## Deployment

### Production Checklist
- [ ] Set `DJANGO_ENV=production`
- [ ] Configure `DJANGO_SECRET_KEY` and `DJANGO_ENCRYPTION_KEY`
- [ ] Set up PostgreSQL database
- [ ] Configure Redis for caching
- [ ] Set `ALLOWED_HOSTS` and `CORS_ALLOWED_ORIGINS`
- [ ] Enable HTTPS with SSL certificates
- [ ] Configure email backend
- [ ] Set up logging and monitoring
- [ ] Run `python manage.py collectstatic`
- [ ] Run `python manage.py test` to verify

### Docker Deployment
```bash
# Build and start all services
docker-compose up -d --build

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

### Manual Deployment
See [DEPLOYMENT.md](DEPLOYMENT.md) for detailed instructions.

## Performance

- **API Response Time**: < 200ms (p95)
- **Cache Hit Rate**: > 85%
- **Database Queries**: < 10 per request
- **Frontend Bundle**: < 500KB gzipped
- **Uptime**: 99.9% target

## Security

- JWT authentication with refresh tokens
- API versioning middleware
- Rate limiting (IP-based + DRF throttling)
- CORS configuration
- Security headers (HSTS, CSP, X-Frame-Options)
- Input validation and sanitization
- SQL injection prevention
- XSS protection
- CSRF protection
- Secrets management via environment variables

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make changes with tests
4. Run test suite
5. Submit a pull request

## License

Proprietary - All rights reserved

## Support

For issues and questions, please open a GitHub issue or contact the development team.

---

**Built with ❤️ by the InvestWise AI Team**