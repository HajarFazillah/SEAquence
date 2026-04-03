# Backend (Spring Boot)

This folder contains the Spring Boot backend for Talkativ.

## Current Status
- ✅ Spring Boot connected to MySQL DB
- ✅ User registration, login, and CRUD API
- ✅ JWT authentication
- ✅ Avatar CRUD API
- ✅ Spring Security configured with JWT filter

---

## Folder Layout

- talkativ-backend/
  Main Spring Boot application (Gradle project).
  - gradlew, gradlew.bat, gradle/wrapper/
    Gradle Wrapper (recommended way to run/build locally).
  - build.gradle
    Dependencies + build configuration.
  - src/main/java/
    Java source code.
    - com/seaquence/talkativ_backend/TalkativBackendApplication.java
      App entry point (@SpringBootApplication).
    - com/seaquence/talkativ_backend/controller/
      REST controllers: UserController, AvatarController.
    - com/seaquence/talkativ_backend/service/
      Business logic: UserService, AvatarService.
    - com/seaquence/talkativ_backend/model/
      JPA entities: User, Avatar.
    - com/seaquence/talkativ_backend/repository/
      Spring Data repositories: UserRepository, AvatarRepository.
    - com/seaquence/talkativ_backend/security/
      JWT utilities and Spring Security config: JwtUtil, SecurityConfig.
    - com/seaquence/talkativ_backend/dto/
      Request/response objects: LoginRequest, LoginResponse,
      RegisterRequest, UserResponse, AvatarRequest, AvatarResponse.
  - src/main/resources/
    App configuration.
    - application.properties        (NOT committed — contains secrets)
    - application.properties.example (copy this to get started)

---

## Local Setup

### 1. Configure application.properties

Copy the example file and fill in your own values:

  cd backend/talkativ-backend/src/main/resources
  copy application.properties.example application.properties

Then open application.properties and set:

  spring.datasource.url=jdbc:mysql://localhost:3307/talkativ
  spring.datasource.username=root
  spring.datasource.password=YOUR_LOCAL_DB_PASSWORD
  jwt.secret=YOUR_JWT_SECRET

⚠️ Never commit application.properties — it is in .gitignore.

### 2. Start the Local Database

Make sure MySQL is running on port 3307 with a database named talkativ.
Ask the team for the actual credentials via KakaoTalk/Discord.

### 3. Run the Backend

  cd backend/talkativ-backend
  .\gradlew.bat clean bootRun

### 4. Test Endpoints

Health check:
  Invoke-WebRequest http://127.0.0.1:8080/health -UseBasicParsing

Register a user:
  Invoke-WebRequest http://127.0.0.1:8080/api/users/register `
    -Method POST `
    -ContentType "application/json" `
    -Body '{"username":"test","email":"test@test.com","password":"1234"}'

Login:
  Invoke-WebRequest http://127.0.0.1:8080/api/users/login `
    -Method POST `
    -ContentType "application/json" `
    -Body '{"email":"test@test.com","password":"1234"}'

---

## API Endpoints

USER ENDPOINTS
  POST    /api/users/register       No auth    Register new user
  POST    /api/users/login          No auth    Login, returns JWT token
  GET     /api/users/{id}           JWT        Get user by ID
  PUT     /api/users/{id}           JWT        Update user
  DELETE  /api/users/{id}           JWT        Delete user

AVATAR ENDPOINTS
  POST    /api/avatars              JWT        Create avatar
  GET     /api/avatars/{userId}     JWT        Get avatar by user ID
  PUT     /api/avatars/{userId}     JWT        Update avatar
  DELETE  /api/avatars/{userId}     JWT        Delete avatar

---

## Notes

- Do NOT commit any real secrets (application.properties, .env, tokens).
  Share credentials via KakaoTalk or Discord only.
- Keep all controllers, services, and repositories under the same base
  package as TalkativBackendApplication so Spring can component-scan them.
- JWT token must be included in the request header for protected endpoints:
  Authorization: Bearer <token>
- jwt.expiration=86400000 means the token expires after 24 hours.