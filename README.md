# AI Voice Agent - High-Volume Outbound Calling System

A Redis-based, high-volume outbound calling system designed for scalability and reliability. This system can handle 10,000-100,000+ calls with adversarial user detection, employment gap analysis, and real-time webhook delivery.

## 🏗️ Architecture Overview

### Redis-First Design
- **Redis** as the core state management system
- **Object Storage** (S3/compatible) for durable data
- **Webhook Delivery** with retry logic and exponential backoff
- **No Database Dependencies** - fully stateless and scalable

### Data Flow
```
UI → Phone Input → Redis State → Twilio Call → AI Agent → Profile Extraction → Object Storage + Webhook
```

## 🚀 Key Features

### Core Capabilities
- **High-Volume Calling**: Handle 10K-100K+ concurrent calls
- **Adversarial Detection**: 0-10 scale scoring of difficult users
- **Employment Gap Analysis**: Detect and fill timeline gaps (e.g., 1977-2004)
- **Real-time State Management**: Redis-based ephemeral state with TTL
- **Reliable Webhook Delivery**: Exponential backoff with retry logic
- **Comprehensive Observability**: Prometheus metrics and structured logging

### Technical Features
- **Rate Limiting**: Prevent spam and abuse
- **Audit Logging**: Compliance-ready call logging
- **Object Storage**: Durable storage for audio, transcripts, and profiles
- **Health Monitoring**: Real-time system health checks
- **Auto-cleanup**: TTL-based data expiration

## 📋 Prerequisites

- **Python 3.9+**
- **Redis 6+**
- **AWS S3** (or S3-compatible storage)
- **Twilio Account** with phone number
- **OpenAI API** access

## 🛠️ Installation

### 1. Clone and Setup
```bash
git clone https://github.com/DerrickAmare/AI_Voice_Agent
cd AI_Voice_Agent

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Install Redis
**macOS:**
```bash
brew install redis
brew services start redis
```

**Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install redis-server
sudo systemctl start redis-server
sudo systemctl enable redis-server
```

### 3. Configure Environment
```bash
cp .env.example .env
# Edit .env with your credentials
```

### Required Environment Variables
| Variable | Description | Required |
|----------|-------------|----------|
| `OPENAI_API_KEY` | OpenAI API key for conversation AI | Yes |
| `TWILIO_ACCOUNT_SID` | Twilio account SID | Yes |
| `TWILIO_AUTH_TOKEN` | Twilio authentication token | Yes |
| `TWILIO_PHONE_NUMBER` | Twilio phone number for calls | Yes |
| `REDIS_URL` | Redis connection URL | Yes |
| `S3_BUCKET_NAME` | S3 bucket for object storage | Yes |
| `AWS_ACCESS_KEY_ID` | AWS access key | Yes |
| `AWS_SECRET_ACCESS_KEY` | AWS secret key | Yes |
| `DEFAULT_WEBHOOK_URL` | Webhook URL for profile delivery | Optional |

## 🏃‍♂️ Quick Start

### 1. Start the System
```bash
# Ensure Redis is running
redis-cli ping  # Should return "PONG"

# Start the application
python main.py
```

### 2. Test the System
```bash
# Run comprehensive tests
python test_redis_system.py

# Test individual components
python -c "
import asyncio
from src.services.redis_state_service import RedisStateService
redis = RedisStateService()
print('Redis Health:', redis.health_check())
"
```

### 3. Make a Test Call
```bash
curl -X POST "http://localhost:8000/api/calls/initiate" \
  -H "Content-Type: application/json" \
  -d '{"phone_number": "+16154846056"}'
```

## 📊 API Endpoints

### Core Endpoints
- `POST /api/calls/initiate` - Initiate outbound call
- `GET /api/calls/status/{call_id}` - Get call status
- `POST /api/calls/webhook/{call_id}` - Twilio webhook handler

### Monitoring Endpoints
- `GET /health` - System health check
- `GET /metrics` - Prometheus metrics
- `GET /api/analytics` - Call analytics
- `GET /api/system/stats` - Detailed system statistics

### Example API Usage
```python
import requests

# Initiate a call
response = requests.post("http://localhost:8000/api/calls/initiate", json={
    "phone_number": "+15551234567",
    "webhook_url": "https://your-webhook.com/profiles"
})

call_data = response.json()
call_id = call_data["call_id"]

# Check call status
status = requests.get(f"http://localhost:8000/api/calls/status/{call_id}")
print(status.json())
```

## 🏗️ System Components

### Redis State Service
- **Call Sessions**: `CALL_SESSION:{call_id}` (TTL: 48h)
- **Rate Limiting**: `RATE_LIMIT:{phone_hash}` (TTL: 24h)
- **Outbox Queue**: `OUTBOX:{event_id}` (TTL: 7 days)

### Object Storage Structure
```
s3://bucket/
├── calls/
│   ├── audio/{date}/{call_id}/recording.wav
│   ├── transcripts/{date}/{call_id}/transcript.json
│   └── profiles/{date}/{call_id}/worker_profile.json
└── audit/{date}/audit_{timestamp}_{id}.json
```

### Webhook Payload Format
```json
{
  "event_type": "worker_profile_completed",
  "timestamp": "2024-01-15T10:30:00Z",
  "call_id": "call_abc123",
  "profile": {
    "phone_hash": "a1b2c3d4",
    "name": "John Smith",
    "current_job": {"title": "Engineer", "company": "Tech Corp"},
    "employment_history": [...],
    "employment_gaps": [...],
    "skills": ["Python", "JavaScript"],
    "adversarial_score": 2.5,
    "confidence_score": 0.85,
    "consent_given": true
  }
}
```

## 📈 Monitoring and Observability

### Prometheus Metrics
- `calls_started_total` - Total calls initiated
- `calls_completed_total` - Total calls completed
- `call_duration_seconds` - Call duration histogram
- `webhook_deliveries_total` - Webhook delivery attempts
- `active_call_sessions` - Current active sessions
- `outbox_queue_size` - Pending webhook deliveries

### Health Checks
```bash
# System health
curl http://localhost:8000/health

# Detailed metrics
curl http://localhost:8000/metrics

# Analytics dashboard
curl http://localhost:8000/api/analytics
```

### Structured Logging
All logs are in JSON format with structured fields:
```json
{
  "timestamp": "2024-01-15T10:30:00Z",
  "level": "info",
  "service": "redis_state",
  "call_id": "call_abc123",
  "phone_hash": "a1b2c3d4",
  "message": "Call session created"
}
```

## 🔧 Configuration

### Redis Configuration
```bash
# Default Redis settings work for development
# For production, consider:
redis-server --maxmemory 2gb --maxmemory-policy allkeys-lru
```

### Object Storage Configuration
```bash
# AWS S3 (default)
AWS_REGION=us-east-1
S3_BUCKET_NAME=ai-voice-agent-prod

# S3-compatible (MinIO, DigitalOcean Spaces, etc.)
S3_ENDPOINT_URL=https://nyc3.digitaloceanspaces.com
```

### Webhook Configuration
```bash
# Retry settings
WEBHOOK_TIMEOUT=30
WEBHOOK_MAX_RETRIES=5

# Delivery endpoint
DEFAULT_WEBHOOK_URL=https://your-api.com/worker-profiles
```

## 🚀 Deployment

### Docker Deployment
```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 8000

CMD ["python", "main.py"]
```

### Environment-Specific Settings
```bash
# Development
ENVIRONMENT=development
LOG_LEVEL=DEBUG
REDIS_URL=redis://localhost:6379

# Production
ENVIRONMENT=production
LOG_LEVEL=INFO
REDIS_URL=redis://redis-cluster:6379
BASE_URL=https://your-domain.com
```

## 🔍 Troubleshooting

### Common Issues

**Redis Connection Failed**
```bash
# Check Redis status
redis-cli ping
sudo systemctl status redis-server

# Check connection
telnet localhost 6379
```

**Object Storage Issues**
```bash
# Test AWS credentials
aws s3 ls s3://your-bucket-name

# Check bucket permissions
aws s3api get-bucket-policy --bucket your-bucket-name
```

**Webhook Delivery Failures**
```bash
# Check outbox queue
curl http://localhost:8000/api/system/stats | jq '.webhook_stats'

# Test webhook endpoint
curl -X POST https://your-webhook.com/test -d '{"test": true}'
```

### Performance Tuning

**Redis Optimization**
```bash
# Memory optimization
redis-cli CONFIG SET maxmemory-policy allkeys-lru
redis-cli CONFIG SET maxmemory 4gb

# Connection pooling
REDIS_URL=redis://localhost:6379?max_connections=100
```

**Webhook Processing**
```bash
# Increase batch size for high volume
WEBHOOK_BATCH_SIZE=50
WEBHOOK_PROCESS_INTERVAL=10
```

## 📝 Development

### Running Tests
```bash
# Full test suite
python test_redis_system.py

# Individual service tests
python -m pytest tests/ -v

# Load testing
python scripts/load_test.py --calls 1000
```

### Code Structure
```
src/
├── services/
│   ├── redis_state_service.py      # Core state management
│   ├── object_storage_service.py   # S3/storage operations
│   ├── webhook_service.py          # Reliable delivery
│   ├── observability_service.py    # Metrics and monitoring
│   └── telephony_service.py        # Twilio integration
├── agents/
│   └── phone_conversation_agent.py # AI conversation logic
└── models/
    └── resume_models.py            # Data models
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- **Twilio** for telephony infrastructure
- **OpenAI** for conversation AI
- **Redis** for high-performance state management
- **FastAPI** for the web framework
- All contributors and users

---

**Ready for high-volume outbound calling with Redis-based architecture! 🚀**
