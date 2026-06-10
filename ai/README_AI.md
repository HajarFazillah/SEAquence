# AI Server (FastAPI)

Talkativ의 AI 서버입니다. **HyperCLOVA X**(CLOVA Studio)를 이용해 한국어 아바타와의 대화 응답을 생성하고, 사용자의 발화를 분석하여 말투(경어법) 수준 평가, 표현 추천, 학습 리포트 등을 제공합니다. 모바일 앱(`mobile/Talkativ`)과 백엔드(`backend/`)에서 이 서버의 REST API를 호출합니다.

> 🇬🇧 영문 버전 (구버전, 일부 항목 업데이트 필요): [README.md](README.md)

---

## Source Code 설명

```
ai/
├── app/
│   ├── main.py              # FastAPI 진입점 (CORS, 라우터 등록)
│   ├── core/
│   │   ├── config.py        # 환경 변수 설정 (.env 로드)
│   │   ├── constants.py      # 상수 정의
│   │   ├── corrections.py    # 표현 교정 규칙
│   │   └── situations.py     # 대화 상황(시나리오) 정의
│   ├── api/v1/                # API 엔드포인트 (각 도메인별 router)
│   │   ├── chat.py            # 아바타 대화
│   │   ├── recommendation.py  # 말투 수준 추천 (25-factor)
│   │   ├── analysis.py        # 발화 분석
│   │   ├── analytics.py       # 세션 분석/통계
│   │   ├── memory.py          # 사용자-아바타 대화 메모리
│   │   ├── vocabulary.py      # 어휘/표현 저장
│   │   ├── starters.py        # 대화 시작 문장 추천
│   │   ├── topics.py          # 대화 주제
│   │   ├── avatars.py         # 아바타 호환성/추천
│   │   ├── revision.py        # 문장 교정/리비전
│   │   ├── progress.py        # 학습 진행도
│   │   ├── integrated.py      # 통합 분석 엔드포인트
│   │   └── prompts.py         # 프롬프트 관련 엔드포인트
│   ├── services/               # 핵심 비즈니스 로직
│   │   ├── chat_service.py             # CLOVA 대화 생성 + 메모리 주입
│   │   ├── clova_service.py            # CLOVA Studio API 클라이언트
│   │   ├── speech_calculator.py        # 25-factor 말투 수준 계산기
│   │   ├── speech_analysis_service.py  # 발화 분석
│   │   ├── memory_service.py           # 대화 메모리 관리
│   │   ├── vocabulary_service.py       # 표현/어휘 저장
│   │   ├── recommendation_service.py   # 말투/주제 추천
│   │   ├── revision_service.py         # 문장 교정
│   │   ├── analytics_service.py        # 세션 통계/리포트
│   │   └── ...                         # 기타 서비스 (감정 분석, 호환성 등)
│   ├── ml/                     # 자연어 처리/임베딩 (sentence-transformers 기반)
│   └── schemas/                # Pydantic 요청/응답 스키마
├── requirements.txt
├── .env.example             # 환경 변수 예시 (.env는 git에 커밋되지 않음)
├── test_all.py               # 전체 엔드포인트 통합 테스트
├── test_api.py                # API 단위 테스트
├── test_identity_stability.py # 아바타 정체성 안정성 회귀 테스트
└── test_custom_situation_regression.py  # 커스텀 시나리오 회귀 테스트
```

말투 수준(경어법) 분석은 KoNLPy/ML 모델이 아닌, **규칙 기반 25-factor 가중치 시스템**(`speech_calculator.py`)으로 구현되어 있습니다. (나이차, 관계, 친밀도, 직장 여부, 상황 등 25개 요소를 점수화하여 `formal`/`polite`/`informal`/`banmal` 4단계로 분류)

---

## How to Build

별도의 컴파일 과정은 없습니다. Python 가상환경에 의존성을 설치하면 됩니다.

```bash
cd ai
python -m venv ../venv
../venv/Scripts/activate      # Windows
# source ../venv/bin/activate  # macOS/Linux

pip install -r requirements.txt
```

---

## How to Install (실행 방법)

1. 환경 변수 파일을 생성합니다.

   ```bash
   cd ai
   copy .env.example .env       # Windows
   # cp .env.example .env        # macOS/Linux
   ```

2. `.env`에 CLOVA Studio API 키와 DB 접속 정보를 입력합니다.

   ```
   NAVER_CLOVA_API_KEY=<발급받은 CLOVA Studio API 키>
   DB_HOST=127.0.0.1
   DB_PORT=3307
   DB_USER=<DB 사용자명>
   DB_PASSWORD=<DB 비밀번호>
   DB_NAME=talkativ
   ```

   - `DB_*` 값은 `/infra`에서 실행 중인 MySQL 컨테이너(`infra/.env`에서 설정한 값)와 일치해야 합니다.

3. 서버를 실행합니다.

   ```bash
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

4. 정상 실행 확인:

   ```bash
   curl http://localhost:8000/
   ```

   `{"name": "Talkativ AI Server", "status": "running", ...}` 응답이 오면 정상입니다.

---

## How to Test

서버 실행 후, 아래 스크립트로 주요 기능을 테스트할 수 있습니다.

```bash
# 전체 엔드포인트 통합 테스트 (서버가 실행 중이어야 함)
python test_all.py

# API 단위 테스트
python test_api.py

# 아바타 정체성 안정성 회귀 테스트
python test_identity_stability.py

# 커스텀 시나리오 회귀 테스트
python test_custom_situation_regression.py
```

간단한 동작 확인은 `curl`로도 가능합니다.

```bash
curl -X POST http://localhost:8000/api/v1/recommendation/speech-level/calculate \
  -H "Content-Type: application/json" \
  -d '{
    "user_age": 22,
    "avatar_age": 35,
    "role": "professor",
    "closeness": "acquaintance",
    "context": "classroom"
  }'
```

---

## Database (사용 데이터)

- AI 서버는 `/infra`에서 실행되는 **MySQL (`talkativ` DB, 포트 3307)** 에 직접 연결하여 사용자/세션/대화 메모리 데이터를 조회·저장합니다. 테이블 구조는 [`infra/README_INFRA.md`](../infra/README_INFRA.md)를 참고하세요.
- 별도의 샘플/시드 데이터는 제공하지 않으며, 모바일 앱을 통해 회원가입 및 대화를 진행하면서 데이터가 누적됩니다.

---

## Open Source 사용 내역

| 이름 | 용도 | 링크 |
|---|---|---|
| FastAPI | REST API 서버 프레임워크 | https://fastapi.tiangolo.com/ |
| Uvicorn | ASGI 서버 (FastAPI 실행) | https://www.uvicorn.org/ |
| Pydantic / pydantic-settings | 요청/응답 데이터 검증 및 환경 변수 관리 | https://docs.pydantic.dev/ |
| httpx / requests | CLOVA Studio 등 외부 API 호출 | https://www.python-httpx.org/ |
| NumPy | 임베딩 벡터 연산 (호환성 분석) | https://numpy.org/ |
| sentence-transformers (ko-sroberta) | 한국어 문장 임베딩 및 유사도 계산 | https://www.sbert.net/ |

또한 대화 응답 생성 및 코칭 피드백에는 네이버 **CLOVA Studio (HyperCLOVA X)** API가 사용됩니다 (오픈소스가 아닌 외부 유료 API).
