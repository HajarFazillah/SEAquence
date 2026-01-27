# 🗣️ Talkativ AI Server

Korean conversation coaching API powered by **Naver HyperCLOVA X**.

## 📁 Project Structure

```
talkativ-ai-prod/
├── app/
│   ├── main.py              # FastAPI entry point
│   ├── api/v1/              # API endpoints
│   │   ├── topics.py        # Topic detection
│   │   ├── analysis.py      # Politeness analysis
│   │   ├── chat.py          # Chat session management
│   │   └── avatars.py       # Avatar information
│   ├── core/
│   │   ├── config.py        # Configuration (Naver API keys)
│   │   └── constants.py     # Topic taxonomy, avatars
│   ├── services/
│   │   ├── clova_service.py      # HyperCLOVA X integration
│   │   ├── speech_service.py     # STT/TTS services
│   │   ├── topic_service.py      # Topic detection
│   │   ├── politeness_service.py # Politeness analysis
│   │   └── chat_service.py       # Chat orchestration
│   └── schemas/
│       └── schemas.py       # Pydantic models
├── tests/
├── requirements.txt
├── .env.example
└── README.md
```

## 🚀 Quick Start

### 1. Clone & Setup

```bash
git clone <your-repo>
cd talkativ-ai-prod

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Naver APIs

```bash
cp .env.example .env
# Edit .env with your Naver API keys
```

### 3. Run Server

```bash
# Development
uvicorn app.main:app --reload --port 8000

# Production
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

### 4. Test API

```bash
# Health check
curl http://localhost:8000/health

# Open docs
open http://localhost:8000/docs
```

---

## 🔑 Naver API Setup

### Step 1: Create Naver Cloud Platform Account

1. Go to [Naver Cloud Platform](https://www.ncloud.com/)
2. Sign up / Login
3. Go to Console

### Step 2: HyperCLOVA X (LLM)

1. Go to [CLOVA Studio](https://clova.ai/studio)
2. Create a new app
3. Get API keys:
   - `NAVER_CLOVA_API_KEY`: X-NCP-CLOVASTUDIO-API-KEY
   - `NAVER_CLOVA_API_KEY_PRIMARY`: X-NCP-APIGW-API-KEY
   - `NAVER_CLOVA_REQUEST_ID`: Your request ID

```env
NAVER_CLOVA_API_KEY=your-clova-api-key
NAVER_CLOVA_API_KEY_PRIMARY=your-primary-api-key
NAVER_CLOVA_REQUEST_ID=your-request-id
NAVER_CLOVA_HOST=https://clovastudio.stream.ntruss.com
NAVER_CLOVA_CHAT_ENDPOINT=/testapp/v1/chat-completions/HCX-003
```

### Step 3: CLOVA Speech (STT) - Optional

1. Go to NCP Console → AI Services → CLOVA Speech
2. Create credentials:

```env
NAVER_SPEECH_CLIENT_ID=your-speech-client-id
NAVER_SPEECH_CLIENT_SECRET=your-speech-client-secret
```

### Step 4: CLOVA Voice (TTS) - Optional

1. Go to NCP Console → AI Services → CLOVA Voice
2. Create credentials:

```env
NAVER_VOICE_CLIENT_ID=your-voice-client-id
NAVER_VOICE_CLIENT_SECRET=your-voice-client-secret
```

---

## 📚 API Endpoints

### Topics

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/topics/detect` | Detect topics from text |
| POST | `/api/v1/topics/recommend` | Get topic recommendations |
| GET | `/api/v1/topics/list` | List all topics |

### Analysis

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/analysis/politeness` | Analyze speech politeness |
| POST | `/api/v1/analysis/relationship` | Analyze user-avatar relationship |

### Chat

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/chat/start` | Start chat session |
| POST | `/api/v1/chat/message` | Send message |
| POST | `/api/v1/chat/end` | End session & get summary |

### Avatars

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/avatars` | List all avatars |
| GET | `/api/v1/avatars/{id}` | Get avatar details |
| GET | `/api/v1/avatars/{id}/formality` | Get formality tips |

---

## 💬 Usage Examples

### Python

```python
import requests

BASE = "http://localhost:8000/api/v1"

# 1. Start chat with avatar
response = requests.post(f"{BASE}/chat/start", json={
    "user_id": "user123",
    "avatar_id": "sujin_friend"  # 수진 (친구)
})
session = response.json()
print(f"Session: {session['session_id']}")
print(f"Greeting: {session['greeting']}")

# 2. Send message
response = requests.post(f"{BASE}/chat/message", json={
    "session_id": session["session_id"],
    "message": "야 오늘 뭐해?",
    "include_feedback": True
})
result = response.json()
print(f"Avatar: {result['avatar_response']['content']}")
print(f"Score: {result['user_message']['feedback']['score']}")

# 3. End chat
response = requests.post(f"{BASE}/chat/end", json={
    "session_id": session["session_id"]
})
summary = response.json()
print(f"Average Score: {summary['average_score']}")
```

### cURL

```bash
# Detect topics
curl -X POST http://localhost:8000/api/v1/topics/detect \
  -H "Content-Type: application/json" \
  -d '{"text": "오늘 중간고사 때문에 도서관에서 공부했어요", "top_k": 3}'

# Analyze politeness
curl -X POST http://localhost:8000/api/v1/analysis/politeness \
  -H "Content-Type: application/json" \
  -d '{"text": "교수님, 질문이 있습니다", "target_role": "professor"}'
```

---

## 🎭 Avatars

| ID | Name | Role | Difficulty | Formality |
|----|------|------|------------|-----------|
| `sujin_friend` | 수진 | Friend | Easy | 반말 |
| `minsu_senior` | 민수 선배 | Senior | Medium | 존댓말 |
| `professor_kim` | 김 교수님 | Professor | Hard | 격식체 |
| `manager_lee` | 이 매니저님 | Boss | Hard | 격식체 |
| `jiwon_junior` | 지원 | Junior | Easy | 반말 |

---

## 🔧 Development

```bash
# Run tests
pytest

# Format code
black app/
ruff check app/

# Type check
mypy app/
```

---

## 📝 Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `NAVER_CLOVA_API_KEY` | Yes* | HyperCLOVA X API key |
| `NAVER_CLOVA_API_KEY_PRIMARY` | Yes* | HyperCLOVA X primary key |
| `NAVER_SPEECH_CLIENT_ID` | No | CLOVA Speech client ID |
| `NAVER_SPEECH_CLIENT_SECRET` | No | CLOVA Speech secret |
| `NAVER_VOICE_CLIENT_ID` | No | CLOVA Voice client ID |
| `NAVER_VOICE_CLIENT_SECRET` | No | CLOVA Voice secret |
| `OPENAI_API_KEY` | No | OpenAI fallback |

*Required for LLM-powered chat

---

## 📄 License

MIT License
