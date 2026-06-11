# Talkativ Backend

Spring Boot backend for **Talkativ**, an AI-assisted Korean conversation coaching
application. The backend manages users, avatars, conversation sessions, saved
vocabulary, and learning mistakes. It also connects the mobile app to CLOVA
Speech and the FastAPI AI server for real-time conversation analysis.

## Main Features

- User registration, login, profile management, and password reset
- JWT creation and request authentication
- Custom avatar creation and management
- Conversation session history
- Saved vocabulary and mistake tracking
- Real-time audio analysis through HTTP and WebSocket APIs
- MySQL persistence with Spring Data JPA

## Technology Stack

| Category | Technology |
| --- | --- |
| Language | Java 17 |
| Framework | Spring Boot 4, Spring Web, Spring Security |
| Database | MySQL 8, Spring Data JPA |
| Authentication | JWT, BCrypt |
| Real-time communication | Spring WebSocket |
| External services | Talkativ FastAPI AI server, Naver CLOVA Speech |
| Build tool | Gradle Wrapper |

## Project Structure

```text
backend/
├── README.md
└── talkativ-backend/
    ├── build.gradle
    ├── gradlew
    ├── gradlew.bat
    └── src/
        ├── main/
        │   ├── java/com/seaquence/talkativ_backend/
        │   │   ├── config/       # WebSocket configuration
        │   │   ├── controller/   # REST API controllers
        │   │   ├── dto/          # Request and response objects
        │   │   ├── entity/       # JPA database entities
        │   │   ├── repository/   # Spring Data repositories
        │   │   ├── security/     # JWT and Spring Security configuration
        │   │   ├── service/      # Business logic and external integrations
        │   │   └── websocket/    # Real-time WebSocket handler
        │   └── resources/
        │       └── application.yml
        └── .env.example
        └── test/
```

## Prerequisites

- Java Development Kit (JDK) 17
- Docker Desktop, or a local MySQL 8 installation
- The Talkativ AI server for real-time analysis features
- CLOVA Speech credentials for speech-to-text features

## Local Setup

### 1. Start MySQL

The repository includes a Docker Compose configuration for MySQL:

```bash
cd SEAquence/infra

# Create infra/.env and add the values below before starting MySQL.
docker compose up -d mysql
```

Required `infra/.env` values:

```properties
MYSQL_ROOT_PASSWORD=your_root_password
MYSQL_DATABASE=talkativ
MYSQL_USER=talkativ
MYSQL_PASSWORD=your_password
```

MySQL is exposed at `localhost:3307`.

### 2. Configure the Backend

Create `backend/talkativ-backend/.env` from the tracked template:

```bash
cp backend/talkativ-backend/.env.example backend/talkativ-backend/.env
```

Then fill in any external-service credentials needed for the evaluation:

```properties
MYSQL_HOST=localhost
MYSQL_PORT=3307
MYSQL_DATABASE=talkativ
MYSQL_USER=talkativ
MYSQL_PASSWORD=your_password

jwt.secret=replace_with_a_long_random_secret
jwt.expiration=86400000

ai.server.url=http://localhost:8000
clova.speech.url=your_clova_speech_endpoint
clova.speech.secret=your_clova_speech_secret

spring.mail.username=your_smtp_username
spring.mail.password=your_smtp_app_password
```

`application.yml` imports this file as Spring properties. Never commit `.env`
files or real credentials. SMTP settings are required only for password-reset
email delivery, and CLOVA Speech settings are required only for speech
recognition.

### 3. Run the Backend

macOS/Linux:

```bash
cd SEAquence/backend/talkativ-backend
./gradlew bootRun
```

Windows:

```powershell
cd SEAquence\backend\talkativ-backend
.\gradlew.bat bootRun
```

The API runs at `http://localhost:8080`. Check it with:

```bash
curl http://localhost:8080/health
```

## API Overview

Most user-specific endpoints expect a JWT in the request header:

```http
Authorization: Bearer <token>
```

| Area | Method and Path | Description |
| --- | --- | --- |
| Health | `GET /health` | Check backend availability |
| Users | `POST /api/users/register` | Register with email and password |
| Users | `POST /api/users/login` | Log in and receive a JWT |
| Users | `GET, PUT /api/users/me` | Read or update the current user |
| Users | `GET /api/users/me/stats` | Get current-user learning statistics |
| Users | `POST /api/users/forgot-password` | Request a password reset code |
| Users | `POST /api/users/reset-password` | Reset a password |
| Social auth | `POST /auth/kakao`, `POST /auth/google` | Social sign-in endpoints |
| Avatars | `GET, POST /api/avatars` | List or create avatars |
| Avatars | `PUT, DELETE /api/avatars/{avatarId}` | Update or delete an avatar |
| Sessions | `GET, POST /api/sessions` | List or create conversation sessions |
| Sessions | `PATCH /api/sessions/{sessionId}/end` | Complete a session |
| Vocabulary | `POST /api/vocabulary` | Save a vocabulary item |
| Vocabulary | `GET /api/vocabulary/me` | List the current user's vocabulary |
| Vocabulary | `DELETE /api/vocabulary/{id}` | Delete a vocabulary item |
| Mistakes | `POST /api/mistakes` | Save a learning mistake |
| Mistakes | `GET /api/mistakes/me` | List the current user's mistakes |
| Mistakes | `GET /api/mistakes/me/weak-areas` | Summarize weak areas |
| Real-time | `POST /realtime/analyze` | Analyze an uploaded audio recording |
| Real-time | `WS /ws/realtime` | Analyze streamed audio messages |

See the controller classes under
`talkativ-backend/src/main/java/com/seaquence/talkativ_backend/controller` for
the complete request and response definitions.

## Build and Test

```bash
cd SEAquence/backend/talkativ-backend
./gradlew clean test
./gradlew build
```

The test suite currently contains a Spring application-context test. Additional
controller and service tests should be added as backend features stabilize.

## Database and Data

The backend uses MySQL 8. The initial schema is provided in
`../infra/mysql/init.sql`, and the main JPA entities are:

- `User`: account, profile, language level, and learning preferences
- `Avatar`: user-created conversation partners and relationship context
- `Session`: conversation-session metadata and completion status
- `Mistake`: corrections and learning feedback from past sessions
- `Vocabulary`: words and examples saved by each user
- `PasswordResetToken`: temporary password-reset verification codes

The repository does not include production user data or a separate sample-data
set. Developers can create local test data through the registration, avatar,
session, vocabulary, and mistake APIs after starting MySQL.

## Open-Source Software

The backend uses the following main open-source projects:

- Spring Boot, Spring Web, Spring Security, Spring WebSocket, and Spring Data JPA
- Hibernate ORM
- MySQL Connector/J
- JJWT
- Lombok
- springdoc-openapi
- Gradle

Exact dependency versions are defined in `talkativ-backend/build.gradle`.

## Current Development Notes

- The backend depends on the AI server for coaching analysis and on CLOVA
  Speech for transcription.
- `application.yml` currently uses Hibernate schema validation, so the database
  schema must exist before the backend starts.
- Spring Security currently permits all routes at the filter-chain level.
  Several controllers still validate JWT headers directly, but route-level
  authorization should be tightened before production deployment.
