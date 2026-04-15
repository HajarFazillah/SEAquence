# Talkativ AI Server v4

Korean conversation coaching AI backend powered by CLOVA Studio (HyperCLOVA X).

---

## Project Structure

```
ai/
├── app/
│   ├── main.py                        # FastAPI entry point
│   ├── core/
│   │   ├── config.py                  # Env vars / settings
│   │   └── clova.py                   # CLOVA Studio API client
│   ├── services/
│   │   ├── speech_calculator.py       # 25-factor rule-based speech level engine
│   │   ├── chat_service.py            # CLOVA chat with memory injection
│   │   ├── memory_service.py          # Per-user/avatar conversation memory
│   │   └── conversation_starters.py   # Smart opening line generator
│   └── api/v1/
│       ├── router.py                  # Combines all routers
│       ├── chat.py                    # /chat endpoints
│       ├── recommendation.py          # /recommendation endpoints
│       ├── memory.py                  # /memory endpoints
│       └── starters.py               # /starters endpoints
├── requirements.txt
├── .env.example
└── README.md
```

---

## Setup

```bash
# 1. Go to the ai directory
cd SEAquence/ai

# 2. Create virtual environment (first time only)
python3 -m venv ../venv

# 3. Activate virtual environment
source ../venv/bin/activate

# 4. Install dependencies
pip install -r requirements.txt

# 5. Set up environment variables
cp .env.example .env
# Edit .env and add your CLOVA API key

# 6. Run the server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

---

## API Endpoints

### Chat
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/chat/message` | Send message, get avatar reply |
| POST | `/api/v1/chat/start` | Start a new session |
| POST | `/api/v1/chat/topic` | Record a conversation topic |
| POST | `/api/v1/chat/speech-level/recommend` | Get speech level recommendation |

### Recommendation (25-factor calculator)
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/recommendation/speech-level/calculate` | Full 25-factor calculation |
| GET | `/api/v1/recommendation/speech-level` | Quick speech level lookup |
| GET | `/api/v1/recommendation/roles` | List all avatar roles |
| GET | `/api/v1/recommendation/closeness-options` | List closeness levels |
| GET | `/api/v1/recommendation/context-options` | List context types |
| GET | `/api/v1/recommendation/speech-levels` | List speech levels with descriptions |

### Memory
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/memory/context` | Get user/avatar memory |
| POST | `/api/v1/memory/update` | Update memory (summary, names) |
| POST | `/api/v1/memory/topic` | Add a topic to memory |
| DELETE | `/api/v1/memory/clear` | Clear all memory for a pair |

### Starters
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/starters/quick` | Template-based starters (fast) |
| POST | `/api/v1/starters/generate` | AI-powered starters via CLOVA |
| GET | `/api/v1/starters/with-memory` | Starters using past conversation memory |
| GET | `/api/v1/starters/greeting` | Simple greeting for current time |

---

## Quick Test

```bash
# Health check
curl http://localhost:8000/health

# Get speech level recommendation
curl -X POST http://localhost:8000/api/v1/recommendation/speech-level/calculate \
  -H "Content-Type: application/json" \
  -d '{
    "user_age": 22,
    "avatar_age": 35,
    "role": "professor",
    "closeness": "acquaintance",
    "context": "classroom"
  }'

# Get quick conversation starters
curl "http://localhost:8000/api/v1/starters/quick?role=senior&avatar_name=민수&interests=게임,음악&speech_level=polite"

# Send a chat message
curl -X POST http://localhost:8000/api/v1/chat/message \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user_001",
    "avatar_id": "avatar_001",
    "avatar_name": "이민수",
    "avatar_role": "senior",
    "avatar_personality": ["친절함", "유머러스"],
    "avatar_interests": ["게임", "음악"],
    "speech_level": "polite",
    "conversation_history": [],
    "message": "안녕하세요! 오늘 어때요?"
  }'
```

---

## Speech Level System (25 Factors)

The speech level calculator uses **explicit rules** — every decision is explainable.

| Category | Factors |
|----------|---------|
| Basic (기본) | Age gap, role, gender norms |
| Relationship (관계) | Closeness, duration, first meeting |
| Professional (직업) | Workplace, context, customer role |
| Situational (상황) | Group size, serious topic, public place |
| Cultural (문화) | Region, online context, generational gap, learner status |

**Output levels:**
- `formal` → 합쇼체/습니다체 (score ≥ 75)
- `polite` → 해요체 (score 55–74)
- `informal` → 해체 (score 35–54)
- `banmal` → 반말 (score < 35)
