# Talkativ AI Server

## Requirements

- **Python 3.11** (recommended) or 3.12


## Quick Start

### 1. Go to the ai folder
```bash
cd ai
```

### 2. Create virtual environment
```bash
# Create venv
python3.11 -m venv venv

# Activate venv
# Mac/Linux:
source venv/bin/activate

# Windows:
.\venv\Scripts\activate
```

### 3. Install dependencies
```bash
pip install --upgrade pip
pip install fastapi uvicorn python-multipart
pip install pydantic pydantic-settings
pip install httpx aiohttp python-dotenv
pip install numpy scikit-learn
pip install torch sentence-transformers
```

### 4. Create `.env` file

### 5. Run server
```bash
python -m uvicorn app.main:app --reload --port 8000
```

### 6. Open API docs

- Swagger UI: http://localhost:8000/docs
- Health check: http://localhost:8000/health

---

## Project Structure
```
ai/
├── app/
│   ├── main.py              # FastAPI entry point
│   ├── api/v1/              # API endpoints
│   │   ├── router.py        # Route aggregator
│   │   ├── avatars.py       # Avatar list
│   │   ├── situations.py    # Situation list
│   │   ├── recommendation.py # Speech level recommendation
│   │   ├── compatibility.py # ML compatibility analysis
│   │   ├── session_chat.py  # Chat session
│   │   └── ...
│   ├── core/
│   │   ├── config.py        # Settings
│   │   ├── constants.py     # Avatars, roles
│   │   └── situations.py    # 11 situations
│   ├── ml/
│   │   └── compatibility_service.py  # ML matching
│   ├── services/
│   │   ├── clova_service.py # HyperCLOVA X API
│   │   └── ...
│   └── schemas/             # Pydantic models
├── .env                     # API keys (DO NOT COMMIT)
└── requirements.txt
```

---

## 🔌 Main API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check |
| `/api/v1/avatars` | GET | List all avatars |
| `/api/v1/situations` | GET | List all situations |
| `/api/v1/recommendation/speech-level` | GET | Get recommended speech level |
| `/api/v1/compatibility/analyze` | POST | Analyze user-avatar compatibility |
| `/api/v1/session/chat` | POST | Send chat message |

---

## 🧪 Test Examples

### Health Check
```bash
curl http://localhost:8000/health
```

### Get Avatars
```bash
curl http://localhost:8000/api/v1/avatars
```

### Get Speech Recommendation
```bash
curl "http://localhost:8000/api/v1/recommendation/speech-level?avatar_id=professor_kim&situation_id=professor_office"
```

### Analyze Compatibility
```bash
curl -X POST "http://localhost:8000/api/v1/compatibility/analyze" \
  -H "Content-Type: application/json" \
  -d '{
    "user": {
      "likes": ["BTS", "카페", "여행"],
      "dislikes": ["정치"]
    },
    "avatar_id": "sujin_friend"
  }'
```

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| `ModuleNotFoundError: No module named 'app'` | Make sure you're in the `ai/` folder |
| `No module named uvicorn` | Run `pip install uvicorn` |
| Port 8000 in use | Use `--port 8001` |
| Python 3.13 errors | Use Python 3.11 instead |

---

## For Backend Team

The AI server is stateless. All user data should be stored in your Spring Boot backend.

### API Call Flow
```
Mobile App → Spring Boot Backend → AI Server → HyperCLOVA X
                    ↓
                 Database
```

### Example: Chat Request from Backend
```java
// Spring Boot example
String aiServerUrl = "http://AI_SERVER_IP:8000";

// POST /api/v1/session/chat
HttpResponse response = httpClient.post(
    aiServerUrl + "/api/v1/session/chat",
    Map.of(
        "session_id", sessionId,
        "user_id", userId,
        "message", userMessage,
        "avatar", avatarData,
        "situation", situationData
    )
);
```

