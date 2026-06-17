# 08 SEAquence - Talkativ  
### Ewha Womans University  
### Computer Science & Engineering  
### Capstone Design Project B (2026-1)

> 🇰🇷 Korean version: [../README.md](../README.md)

---

## 📌 Project Overview

**Project Name** <br>Talkativ: An AI-Powered Context-Aware Avatar-Based Conversational Simulation and Coaching System for Enhancing Korean Communication Skills Among Multinational Users

**Description** <br>Talkativ is an AI-powered mobile coaching app designed for non-native Korean learners living in Korea. Users engage in 1:1 conversational simulations with AI avatars configured with specific relationship roles and situational contexts, across two modes: text-based chat and real-time voice conversation. HyperCLOVA X analyzes each utterance for context, relationship, and speech register, providing immediate coaching feedback. A learning report is generated at the end of each session.

---

## 🎯 Project Goals

- Reduce the **linguistic and psychological barriers** Korean learners face in real conversational settings
- Support learners in choosing appropriate **speech registers and expressions** based on relationship dynamics (seniority, age, familiarity)
- Build a **context-aware Korean speech coaching system** beyond simple translation or chatbot interaction

---

## 🧠 Core Technologies

### 1. AI Avatar Conversation System
- Role-specific speech style, personality reflection, and context awareness
- Response generation powered by the Korean LLM **HyperCLOVA X**

### 2. Relationship & Honorifics Analysis Engine
- Morpheme-level analysis using **KoNLPy** for accurate verb endings and particles
- Hierarchical relationship analysis based on user-defined role settings
- Speech register appropriateness validation per relationship type

### 3. Real-Time Speech Recognition & Correction
- Live speech recognition via **Naver CLOVA Speech**
- Situation-specific vocabulary and expression recommendations by HyperCLOVA X
- Native speaker expression comparison and correction feedback

### 4. Personalized Learning Management
- Per-session scoring: speech accuracy, vocabulary, and naturalness
- Repeated error pattern analysis and learning report generation

---

## 🧩 Project Scope

- **Capstone A (Completed):**
  - Problem definition and user requirements analysis
  - System architecture design and core technology definition
  - Differentiation and in-depth interview preparation

- **Capstone B (Completed):**
  - React Native mobile client (chat mode, real-time mode, session history, profile management)
  - Spring Boot backend and FastAPI AI server implementation
  - Avatar scenario editor, onboarding screen, and personalized learning reports
  - Prototype completion and user testing
  - Final report submission and graduation presentation completed

---

## 👥 Team Members

- **Siti Hajar Asyiqin Binti Fazillah** – Team Leader
- **Heimvichit, Nunnalin**
- **Yuzana Win**

### 👩‍🏫 Team Supervisor
- **Prof. Ban Hyo-kyung**

---

## 📁 Repository Structure

```
SEAquence/
├── mobile/                          # React Native mobile client (Talkativ)
├── backend/                         # Spring Boot backend server
├── ai/                              # FastAPI AI server (HyperCLOVA X & CLOVA Speech integration)
├── infra/                           # Infrastructure configuration
├── doc/                             # Project documentation
│   ├── README_EN.md                 # English README (this file)
│   ├── ProjectScenario.md           # Project scenario and SW package definitions
│   └── GroundRules.md               # Team collaboration rules
└── README.md                        # Korean README
```

---

## 📎 Notes

- This repository is the **official project asset for team collaboration and Capstone coursework**.
- This project is conducted as an academic capstone design course assignment.

---

This project was completed as part of the Capstone Design B course (2026-1).
