# Backend (Spring Boot)

This folder contains the Spring Boot backend for Talkativ.

Spring S0 status:
- Backend app runs locally.
- Health check endpoint is available: `GET /health` → `200` with a small JSON body.

## Folder layout

- `talkativ-backend/`
  Main Spring Boot application (Gradle project).
  - `gradlew`, `gradlew.bat`, `gradle/wrapper/`
    Gradle Wrapper (recommended way to run/build locally).
  - `build.gradle` (or `build.gradle.kts`)
    Dependencies + build configuration.
  - `src/main/java/`
    Java source code.
    - `com/seaquence/talkativ_backend/TalkativBackendApplication.java`
      App entry point (`@SpringBootApplication`).
    - `com/seaquence/talkativ_backend/HealthController.java`
      Health endpoint (`GET /health`).
  - `src/main/resources/`
    App configuration (e.g., `application.yml`).

## How to run (local)

1) Start the local database (see `/infra` docs).
2) Configure required local secrets/credentials (ask the team or follow the internal setup doc).
3) Run the backend:
```powershell
cd backend/talkativ-backend
.\gradlew.bat clean bootRun
```
4) Test:
(powershell)
Invoke-WebRequest http://127.0.0.1:8080/health -UseBasicParsing
Expected: HTTP 200.

Extra Notes / conventions
- Do not commit any real secrets (.env, credentials, tokens). Keep them local and share via a secure channel.
If you change package names, keep controllers/services under the same base package as TalkativBackendApplication so Spring can component-scan them.
