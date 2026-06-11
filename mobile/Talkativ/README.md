# Talkativ Mobile (React Native)

Talkativ의 모바일 클라이언트입니다. 사용자는 회원가입/프로필 설정 후 AI 아바타와 텍스트 채팅 또는 실시간 음성 대화를 진행하며, 발화에 대한 말투(경어법) 분석과 학습 리포트를 확인할 수 있습니다. 백엔드(Spring Boot, `backend/`)와 AI 서버(FastAPI, `ai/`)의 REST API를 호출합니다.

---

## Source Code 설명

```
mobile/Talkativ/
├── App.tsx                   # 앱 진입점
├── index.js                  # React Native 엔트리 등록
├── android/                   # Android 네이티브 프로젝트
├── ios/                       # iOS 네이티브 프로젝트
├── .env.example               # 환경 변수 예시 (.env는 git에 커밋되지 않음)
└── src/
    ├── navigation/
    │   ├── AppNavigator.tsx    # 전체 화면 라우팅 (인증, 온보딩, 메인 등)
    │   └── MainTabs.tsx         # 메인 하단 탭 (홈/대화/프로필 등)
    ├── screens/                 # 화면 단위 컴포넌트
    │   ├── WelcomeScreen / LoginScreen / SignUpScreen / ForgotPasswordScreen   # 인증
    │   ├── CreateProfileStep1Screen / CreateProfileStep2Screen                 # 온보딩 프로필 설정
    │   ├── HomeScreen                                                          # 홈 (추천 아바타/주제)
    │   ├── AvatarScreen / AvatarSelectionScreen / AvatarDetailScreen
    │   │   / AvatarCompatibilityScreen / CreateAvatarScreen                    # 아바타 목록/상세/호환성/커스텀 생성
    │   ├── SituationSelectionScreen / CreateSituationScreen / ScenarioIntroScreen  # 대화 상황(시나리오) 선택/생성
    │   ├── ChatScreen / RealtimeScreen / RealtimeSessionScreen                 # 텍스트 채팅 / 실시간 음성 대화
    │   ├── ConversationSummaryScreen / ConversationHistoryScreen / FeedbackScreen / AnalyticsScreen  # 세션 요약/이력/피드백/통계
    │   ├── SpeechRecommendationScreen / SavedVocabularyScreen                  # 말투 추천, 저장한 표현
    │   └── MyProfileScreen / ProfilesScreen / EditProfileScreen / EditInterestsScreen  # 프로필 관리
    ├── components/             # 공통 UI 컴포넌트 (Button, Card, Header, Tag, ProgressBar 등)
    ├── services/                # API 클라이언트
    │   ├── api.ts                       # 아바타/상황/추천 등 AI 서버 호출
    │   ├── apiAuth.ts                    # 로그인/회원가입/인증
    │   ├── apiUser.ts                    # 사용자 프로필
    │   ├── apiSession.ts                 # 대화 세션
    │   ├── apiVocabulary.ts              # 저장 표현(단어장)
    │   ├── apiMistakes.ts                # 오류/교정 기록
    │   ├── clovaService.ts               # CLOVA 음성 관련 호출
    │   ├── audioCapture.ts               # 실시간 음성 녹음
    │   ├── realtimeAnalysisService.ts    # 실시간 발화 분석
    │   ├── honorificService.ts           # 말투(경어법) 관련 헬퍼
    │   └── conversationPreview.ts / personalizationHistory.ts
    ├── constants/index.ts       # 서버 주소, 색상, 아바타/상황/말투 레벨 정의
    ├── hooks/                    # 커스텀 훅 (useHomeData 등)
    └── utils/                    # 유틸 함수 (avatarDifficulty 등)
```

---

## How to Build

```bash
cd mobile/Talkativ
npm install
```

- Android: Android Studio + Android SDK 설치 필요
- iOS (macOS): `bundle install` 후 `bundle exec pod install` 로 CocoaPods 의존성 설치 필요

---

## How to Install (실행 방법)

1. 환경 변수 파일을 생성합니다.

   ```bash
   cd mobile/Talkativ
   copy .env.example .env       # Windows
   # cp .env.example .env        # macOS/Linux
   ```

2. `.env`에 백엔드/AI 서버가 실행 중인 PC의 로컬 IP를 입력합니다. (모바일 기기/에뮬레이터에서 접근 가능한 주소여야 합니다.)

   ```
   SPRING_SERVER_IP=<로컬 IP, 예: 192.168.0.10>
   AI_SERVER_IP=<로컬 IP, 예: 192.168.0.10>
   ```

   - 백엔드(`backend/`, 8080 포트)와 AI 서버(`ai/`, 8000 포트)가 먼저 실행되어 있어야 합니다.
   - Android 에뮬레이터에서 PC의 localhost에 접속하려면 `10.0.2.2`를 사용할 수 있습니다.

3. Metro 번들러를 실행합니다.

   ```bash
   npm start
   ```

4. 새 터미널에서 앱을 빌드/실행합니다.

   ```bash
   npm run android   # Android
   npm run ios       # iOS (macOS)
   ```

---

## How to Test

```bash
npm test
```

- Jest 기반 단위 테스트 (`__tests__/App.test.tsx`)
- 코드 스타일 검사:

  ```bash
  npm run lint
  ```

---

## Database (사용 데이터)

모바일 앱은 자체 데이터베이스를 갖지 않으며, 모든 사용자/세션/대화 데이터는 백엔드(Spring Boot)와 AI 서버(FastAPI)를 통해 MySQL(`talkativ` DB)에 저장됩니다. 데이터베이스 구성은 [`infra/README.md`](../../infra/README.md)를 참고하세요.

---

## Open Source 사용 내역

| 이름 | 용도 | 링크 |
|---|---|---|
| React Native | 모바일 앱 프레임워크 | https://reactnative.dev/ |
| React Navigation | 화면 라우팅 (스택/탭 네비게이션) | https://reactnavigation.org/ |
| Axios | 백엔드/AI 서버 REST API 호출 | https://axios-http.com/ |
| AsyncStorage | 로컬 저장소 (로그인 토큰 등) | https://react-native-async-storage.github.io/async-storage/ |
| react-native-config | `.env` 환경 변수 관리 | https://github.com/lugg/react-native-config |
| react-native-nitro-sound | 오디오 녹음/재생 (실시간 음성 모드) | https://github.com/mrousavy/react-native-nitro-sound |
| react-native-fs | 파일 시스템 접근 | https://github.com/itinance/react-native-fs |
| react-native-image-picker | 프로필 이미지 선택 | https://github.com/react-native-image-picker/react-native-image-picker |
| react-native-svg | SVG 아이콘/그래픽 렌더링 | https://github.com/software-mansion/react-native-svg |
| lucide-react-native | 아이콘 세트 | https://lucide.dev/ |
| @react-native-google-signin / @react-native-kakao | 구글/카카오 소셜 로그인 | https://github.com/react-native-google-signin/google-signin / https://github.com/kakao/react-native-kakao |
| Jest | 단위 테스트 프레임워크 | https://jestjs.io/ |
