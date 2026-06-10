# Infra (인프라)

Talkativ 프로젝트의 로컬 개발용 인프라 설정입니다. Docker Compose로 MySQL 데이터베이스를 띄우고, 백엔드(Spring Boot)와 AI 서버(FastAPI)가 이 데이터베이스에 접속하여 사용자 정보·세션·대화 기록 등을 저장합니다.

---

## Source Code 설명

```
infra/
├── compose.yml      # Docker Compose 설정 (MySQL 컨테이너 정의)
├── .env.example     # 환경 변수 예시 파일 (.env는 git에 커밋되지 않음)
└── mysql/
    └── init.sql     # 컨테이너 최초 실행 시 자동 실행되는 DB 초기화 스크립트
```

- `compose.yml`: `mysql:8.0` 이미지를 기반으로 `seaq-mysql` 컨테이너를 실행합니다. 호스트의 `3307` 포트를 컨테이너의 `3306` 포트(MySQL 기본 포트)에 연결합니다.
- `mysql/init.sql`: 컨테이너가 처음 생성될 때 `/docker-entrypoint-initdb.d/init.sql`로 마운트되어 자동 실행되며, `talkativ` 데이터베이스와 필요한 테이블을 생성합니다.

---

## How to Build

별도의 빌드 과정은 없습니다. `mysql:8.0` 공식 이미지를 그대로 사용합니다.

```bash
cd infra
docker compose pull
```

---

## How to Install (실행 방법)

1. `infra/.env` 파일을 생성하고 아래 값을 채웁니다 (`.env.example` 참고).

   ```
   MYSQL_ROOT_PASSWORD=<root 비밀번호>
   MYSQL_DATABASE=talkativ
   MYSQL_USER=<DB 사용자명>
   MYSQL_PASSWORD=<DB 사용자 비밀번호>
   ```

2. 컨테이너를 실행합니다.

   ```bash
   cd infra
   docker compose up -d
   ```

3. 정상 실행 확인:

   ```bash
   docker compose ps
   ```

   `seaq-mysql` 컨테이너가 `0.0.0.0:3307->3306/tcp`로 떠 있으면 정상입니다.

4. 백엔드(`backend/`)와 AI 서버(`ai/`)의 DB 접속 설정에서 호스트는 `localhost`, 포트는 `3307`, 데이터베이스명은 `talkativ`로 지정합니다.

---

## How to Test

MySQL 클라이언트로 접속하여 `init.sql`이 정상적으로 적용되었는지 확인합니다.

```bash
docker exec -it seaq-mysql mysql -u root -p talkativ
```

```sql
SHOW TABLES;
```

아래 7개 테이블이 모두 보이면 정상입니다: `users`, `sessions`, `session_utterance`, `topic_preferences`, `relationship_analysis`, `session_mistakes`, `feedback`.

컨테이너를 종료/삭제하려면:

```bash
docker compose down        # 컨테이너만 종료
docker compose down -v     # 컨테이너 + 데이터 볼륨까지 삭제 (DB 초기화)
```

---

## Database (사용 데이터)

`mysql/init.sql`에서 생성하는 테이블 구성:

| 테이블 | 설명 |
|---|---|
| `users` | 사용자 계정 정보, 프로필(나이, 성별, 한국어 수준), 관심사/비선호 주제, 개인정보 동의 여부 |
| `sessions` | 대화 세션 정보 (사용자, 아바타, 상황, 시작/종료 시간 등) |
| `session_utterance` | 세션별 발화(대화 turn) 기록 |
| `topic_preferences` | 사용자별 선호/비선호 주제 |
| `relationship_analysis` | 사용자-아바타 관계 및 말투 수준 분석 결과 |
| `session_mistakes` | 세션 중 발생한 표현/말투 오류 기록 |
| `feedback` | 세션 종료 후 생성되는 학습 피드백/리포트 |

샘플 데이터(seed data)는 별도로 제공하지 않으며, 앱을 사용하면서 회원가입/대화를 진행하면 데이터가 누적됩니다.

---

## Open Source 사용 내역

| 이름 | 용도 | 링크 |
|---|---|---|
| Docker / Docker Compose | 로컬 개발 환경에서 MySQL 컨테이너 실행 및 관리 | https://www.docker.com/ |
| MySQL 8.0 | 사용자/세션/대화 데이터를 저장하는 관계형 데이터베이스 | https://www.mysql.com/ |
