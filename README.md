# Plant Care Application - Backend API

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)](https://fastapi.tiangolo.com/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15+-blue.svg)](https://www.postgresql.org/)
[![Redis](https://img.shields.io/badge/Redis-7+-red.svg)](https://redis.io/)
[![Docker](https://img.shields.io/badge/Docker-20+-blue.svg)](https://www.docker.com/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

A comprehensive backend API for the Plant Care Application built with FastAPI, featuring plant management, care scheduling, AI-powered features, and community interactions.

## 🌱 Features

### Core Functionality
- **Plant Management**: Add, manage, and track personal plant collections
- **Plant Identification**: AI-powered plant identification using multiple APIs
- **Care Scheduling**: Automated care reminders and task management
- **Health Monitoring**: Plant health tracking and diagnosis
- **Growth Tracking**: Photo journaling and growth milestone tracking

### Smart Features
- **AI Chat Assistant**: Plant care advice and guidance
- **Weather Integration**: Weather-based care adjustments
- **Smart Recommendations**: Personalized plant and care suggestions
- **Automation Rules**: Automated care scheduling based on conditions

### Social Features
- **Community Feed**: Share plant photos and experiences
- **Expert Advice**: Get help from plant care experts
- **Social Interactions**: Like, comment, and share plant content

### Premium Features
- **Advanced Analytics**: Detailed plant care insights
- **Unlimited Plants**: No limits on plant collection size
- **Priority Support**: Faster response times and premium features
- **Family Sharing**: Share plants with family members

## 🏗️ Architecture

### Modular Monolith Design
```
plant-care-backend/
├── app/
│   ├── shared/              # Shared kernel (common utilities)
│   ├── modules/             # Domain modules
│   │   ├── user_management/
│   │   ├── plant_management/
│   │   ├── care_management/
│   │   ├── health_monitoring/
│   │   ├── growth_tracking/
│   │   ├── community_social/
│   │   ├── ai_smart_features/
│   │   ├── weather_environmental/
│   │   ├── analytics_insights/
│   │   ├── notification_communication/
│   │   ├── payment_subscription/
│   │   └── content_management/
│   ├── background_jobs/     # Celery tasks
│   ├── api/                 # API layer
│   └── monitoring/          # Health checks & monitoring
```

### Technology Stack
- **Framework**: FastAPI 0.104+ with async/await support
- **Database**: PostgreSQL 15+ with SQLAlchemy 2.0
- **Cache**: Redis 7+ for caching and session storage
- **Background Jobs**: Celery with Redis broker
- **Authentication**: Supabase Auth with JWT tokens
- **File Storage**: Supabase Storage for images
- **Monitoring**: Prometheus metrics, Grafana dashboards
- **API Documentation**: OpenAPI/Swagger auto-generated

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- Docker & Docker Compose
- PostgreSQL 15+
- Redis 7+

### Installation

1. **Clone the repository**
```bash
git clone https://github.com/plantcare/backend.git
cd plant-care-backend
```

2. **Set up environment variables**
```bash
cp .env.example .env
# Edit .env with your configuration
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Start with Docker Compose**
```bash
docker-compose up -d
```

5. **Run database migrations**
```bash
alembic upgrade head
```

6. **Seed the database (optional)**
```bash
python scripts/seed_database.py
```

7. **Access the API**
- API Documentation: http://localhost:8000/docs
- Health Check: http://localhost:8000/health/live
- Flower (Celery Monitor): http://localhost:5555
- Grafana Dashboard: http://localhost:3000

## 🔧 Development

### Local Development Setup

1. **Create virtual environment**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. **Install development dependencies**
```bash
pip install -r requirements.txt
pip install -e .
```

3. **Set up pre-commit hooks**
```bash
pre-commit install
```

4. **Run the application**
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test types
pytest tests/unit/
pytest tests/integration/
pytest tests/e2e/
```

### Code Quality

```bash
# Format code
black app/
isort app/

# Lint code
flake8 app/
mypy app/

# Security check
bandit -r app/
```

## 📚 API Documentation

### Authentication
All API endpoints require authentication via JWT tokens from Supabase Auth.

```bash
# Login
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "password"}'
```

### Plant Management
```bash
# Get user's plants
curl -X GET "http://localhost:8000/api/v1/plants" \
  -H "Authorization: Bearer YOUR_TOKEN"

# Add a new plant
curl -X POST "http://localhost:8000/api/v1/plants" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name": "My Plant", "species": "Monstera deliciosa"}'

# Identify plant from image
curl -X POST "http://localhost:8000/api/v1/plants/identify" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "image=@plant_photo.jpg"
```

### Care Management
```bash
# Get care schedule
curl -X GET "http://localhost:8000/api/v1/care/schedule" \
  -H "Authorization: Bearer YOUR_TOKEN"

# Complete care task
curl -X POST "http://localhost:8000/api/v1/care/tasks/{task_id}/complete" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Community Features
```bash
# Get community feed
curl -X GET "http://localhost:8000/api/v1/community/feed" \
  -H "Authorization: Bearer YOUR_TOKEN"

# Create post
curl -X POST "http://localhost:8000/api/v1/community/posts" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"content": "Look at my beautiful plant!", "plant_id": "plant_uuid"}'
```

## 🔐 Security

### Authentication & Authorization
- JWT tokens with 30-minute expiration
- Refresh tokens with 7-day expiration
- Row-level security (RLS) in database
- API key rotation for external services

### Data Protection
- All passwords hashed with bcrypt
- Sensitive data encrypted at rest
- HTTPS enforcement in production
- Rate limiting on all endpoints

### API Security
- Input validation with Pydantic
- SQL injection prevention
- XSS protection
- CORS configuration
- Security headers middleware

## 🚀 Deployment

### Docker Production

```bash
# Build production image
docker build -t plant-care-api .

# Run with production compose
docker-compose -f docker-compose.prod.yml up -d
```

### Environment Variables
Key environment variables for production:

```bash
# Application
APP_ENV=production
DEBUG=false
SECRET_KEY=your-secret-key

# Database
DATABASE_URL=postgresql+asyncpg://user:pass@host:5432/db

# Supabase
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-supabase-key

# External APIs
PLANTNET_API_KEY=your-plantnet-key
OPENWEATHER_API_KEY=your-weather-key
OPENAI_API_KEY=your-openai-key

# Notifications
FCM_SERVER_KEY=your-fcm-key
SENDGRID_API_KEY=your-sendgrid-key

# Payments
RAZORPAY_KEY_ID=your-razorpay-key
STRIPE_SECRET_KEY=your-stripe-key
```

### Health Checks
- **Liveness**: `/health/live`
- **Readiness**: `/health/ready`
- **Startup**: `/health/startup`
- **Detailed**: `/health/detailed`

## 📊 Monitoring

### Metrics
- Prometheus metrics at `/metrics`
- Custom business metrics
- Performance monitoring
- Error tracking

### Logging
- Structured JSON logging
- Request/response logging
- Error logging with context
- Performance logging

### Alerting
- Health check failures
- High error rates
- Performance degradation
- External API failures

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Development Guidelines
- Follow PEP 8 style guidelines
- Write comprehensive tests
- Update documentation
- Use conventional commits
- Ensure all checks pass

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [FastAPI](https://fastapi.tiangolo.com/) - Web framework
- [SQLAlchemy](https://www.sqlalchemy.org/) - Database ORM
- [Supabase](https://supabase.com/) - Backend services
- [Celery](https://docs.celeryq.dev/) - Task queue
- [Redis](https://redis.io/) - Cache and message broker
- [PlantNet](https://plantnet.org/) - Plant identification
- [OpenWeatherMap](https://openweathermap.org/) - Weather data

## 📞 Support

- 📧 Email: support@plantcare.com
- 📚 Documentation: https://docs.plantcare.com
- 🐛 Issues: https://github.com/plantcare/backend/issues
- 💬 Discussions: https://github.com/plantcare/backend/discussions

---

Made with ❤️ by the Plant Care Team
>>>>>>> 256981f (Initial commit for plant care backend)
