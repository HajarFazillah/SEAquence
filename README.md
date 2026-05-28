# 08 SEAquence - Talkativ  
### Ewha Womans University  
### Computer Science & Engineering  
### Capstone Design Project B (2026-1)

> 🇬🇧 English version: [README_EN.md](README_EN.md)

---

## 📌 프로젝트 개요 (Project Overview)

**프로젝트명** <br>Talkativ - 다국적 사용자의 한국어 의사소통을 돕는 AI 기반 맥락 인식 대화 시뮬레이션 및 코칭 시스템

**프로젝트 내용** <br>한국에 거주하는 비원어민 한국어 학습자를 위한 AI 기반 모바일 코칭 앱입니다. 사용자는 관계·상황이 설정된 AI 아바타와 1:1 대화 시뮬레이션을 진행하며, 텍스트 채팅과 실시간 음성 대화 두 가지 모드를 지원합니다. HyperCLOVA X가 맥락·관계·말투를 분석해 즉각적인 코칭 피드백을 제공하고, 세션 종료 후 학습 리포트를 생성합니다.

---

## 🎯 프로젝트 목적 (Project Goals)

- 한국어 학습자가 실제 대화 상황에서 느끼는 **언어적·심리적 부담 완화**
- 대화 상대와의 관계(지위, 나이, 친밀도)를 고려한 말투·표현 학습 지원
- 단순 번역이나 챗봇이 아닌, **대화 맥락 기반 한국어 코칭 시스템 설계**

---

## 🧠 핵심 기술 개요 (Core Technologies)

### 1. AI 아바타 대화 시스템
- 역할별 말투, 성격 반영, 문맥 인식
- 한국 LLM **HyperCLOVA X** 기반 응답 생성

### 2. 관계·경어법 분석 엔진
- KoNLPy 형태소 분석으로 어미/조사 추출
- 역할 기반 위계 관계 분석 및 말투 적절성 검사

### 3. 실시간 음성 인식 및 교정
- **Naver CLOVA Speech** 기반 실시간 발화 인식
- HyperCLOVA X 기반 상황별 어휘·표현 추천 및 원어민 문장 비교

### 4. 개인화 학습 관리
- 세션별 기록 및 점수 추적 (말투 정확도, 어휘력, 자연스러움)
- 반복 실수 패턴 분석 및 학습 리포트 생성

---

## 🧩 프로젝트 범위 (Scope)

- **Capstone A (완료):**
  - 문제 정의 및 사용자 요구 분석
  - 시스템 구조 설계 및 핵심 기술 정의
  - 차별성 정립 및 심층인터뷰 준비

- **Capstone B (완료 및 진행 중):**
  - React Native 모바일 클라이언트 구현 (채팅·실시간 모드, 세션 이력, 프로필)
  - Spring Boot 백엔드 및 FastAPI AI 서버 구현
  - 아바타 시나리오 에디터, 온보딩 화면, 맞춤형 학습 리포트
  - 프로토타입 완성 및 사용자 테스트

---

## 👥 팀 구성 (Team Members)

- **Siti Hajar Asyiqin Binti Fazillah** – Team Leader
- **Heimvichit, Nunnalin**
- **Yuzana Win**

### 👩‍🏫 Team Supervisor
- **반효경 교수님**

---

## 📁 저장소 구성 (Repository Structure)

```
SEAquence/
├── mobile/                          # React Native 모바일 클라이언트 (Talkativ)
├── backend/                         # Spring Boot 백엔드 서버
├── ai/                              # FastAPI AI 서버 (HyperCLOVA X, CLOVA Speech 연동)
├── infra/                           # 인프라 설정
├── README.md                        # 한국어 README
├── README_EN.md                     # 영문 README
├── Project-Scenario.md              # 프로젝트 시나리오 및 SW 패키지 정의
├── GroundRules.md                   # 팀 협업 규칙
├── 08-SEAquence-2차보고서v2-SitiHajarAsyiqin.pdf   # 2차 보고서
└── 08-SEAquence-2차 보고서-SitiHajarAsyiqin.pdf    # 2차 보고서 (초안)
```

---

## 📎 참고 사항 (Notes)

- 본 저장소는 **팀 협업 및 Capstone 과제 수행을 위한 공식 프로젝트 자산**입니다.
- 본 프로젝트는 교육 목적의 캡스톤 디자인 과제로 수행됩니다.

---

This repository will continue to evolve as the project progresses 🚀
