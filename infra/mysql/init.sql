-- MySQL initialization script for Talkativ application
-- This script creates the necessary database and tables for storing user profiles, conversation sessions, utterances, topic preferences, relationship analysis results, and feedback.

CREATE DATABASE IF NOT EXISTS talkativ;
USE talkativ;

-- ------------------------------------------------------------
-- 1. Users
-- Stores user identity, profile, and privacy consent
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS users (
    user_id          VARCHAR(36)   PRIMARY KEY,
    username         VARCHAR(50)   NOT NULL UNIQUE,
    email            VARCHAR(100)  NOT NULL UNIQUE,
    password         VARCHAR(255),
    provider         VARCHAR(10)   DEFAULT 'local',
    avatar_url       VARCHAR(500),
    native_lang      VARCHAR(10),
    target_lang      VARCHAR(10),
    korean_level     VARCHAR(20)   DEFAULT 'intermediate',
    age              VARCHAR(10),
    gender           VARCHAR(20),
    memo             VARCHAR(1000),
    interests        VARCHAR(1000),
    dislikes         VARCHAR(1000),
    privacy_consent  TINYINT(1)    DEFAULT 0,
    created_at       DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at       DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- ------------------------------------------------------------
-- 2. User-created avatars
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS user_avatar (
    avatar_id                BIGINT       PRIMARY KEY AUTO_INCREMENT,
    user_id                  VARCHAR(36)  NOT NULL,
    name_ko                  VARCHAR(50),
    name_en                  VARCHAR(50),
    age                      VARCHAR(10),
    gender                   VARCHAR(10),
    avatar_type              VARCHAR(20),
    avatar_bg                VARCHAR(20),
    icon                     VARCHAR(30),
    role                     VARCHAR(50),
    custom_role              VARCHAR(50),
    relationship_description TEXT,
    difficulty               VARCHAR(20),
    description              TEXT,
    personality_traits       TEXT,
    speaking_style           TEXT,
    interests                TEXT,
    dislikes                 TEXT,
    memo                     TEXT,
    formality_to_user        VARCHAR(20),
    formality_from_user      VARCHAR(20),
    bio                      TEXT,
    is_active                TINYINT(1)   DEFAULT 1,
    created_at               DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at               DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);

-- ------------------------------------------------------------
-- 3. Session
-- A single real-time conversation session
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS sessions (
    session_id      VARCHAR(36)  PRIMARY KEY,
    user_id         VARCHAR(36)  NOT NULL,
    avatar_id       VARCHAR(100) NOT NULL,
    avatar_name     VARCHAR(100) NOT NULL,
    avatar_icon     VARCHAR(50)  NOT NULL,
    avatar_bg       VARCHAR(20)  NOT NULL,
    situation       VARCHAR(200) NOT NULL,
    mood            INT          NOT NULL DEFAULT 50,
    difficulty      VARCHAR(20)  NOT NULL DEFAULT 'medium',
    status          VARCHAR(20)  NOT NULL DEFAULT 'active',
    session_type    VARCHAR(20)  NOT NULL DEFAULT 'chat',
    started_at      DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    ended_at        DATETIME,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS chat_turns (
    id           BIGINT       PRIMARY KEY AUTO_INCREMENT,
    session_id   VARCHAR(255) NOT NULL,
    turn_number  INT          NOT NULL,
    role         VARCHAR(50)  NOT NULL,
    message      TEXT         NOT NULL,
    created_at   TIMESTAMP    DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_session_turn (session_id, turn_number)
);

-- ------------------------------------------------------------
-- 4. Saved vocabulary
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS vocabulary (
    id           BIGINT        PRIMARY KEY AUTO_INCREMENT,
    user_id      VARCHAR(64)   NOT NULL,
    kind         VARCHAR(16)   NOT NULL,
    word         VARCHAR(255)  CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
    meaning      TEXT          CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci,
    example      TEXT          CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci,
    from_avatar  VARCHAR(128)  CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci,
    session_id   VARCHAR(255),
    created_at   DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uk_vocabulary_user_kind_word (user_id, kind, word)
);

-- ------------------------------------------------------------
-- 5. Learning mistakes used by the Spring backend
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS mistakes (
    id               BIGINT       PRIMARY KEY AUTO_INCREMENT,
    session_id       VARCHAR(255) NOT NULL,
    user_id          VARCHAR(36)  NOT NULL,
    turn_number      INT,
    original_text    TEXT         CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
    corrected_text   TEXT         CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
    correction_type  VARCHAR(50),
    severity         VARCHAR(20),
    explanation      TEXT         CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci,
    tip              TEXT         CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci,
    created_at       DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_mistakes_user (user_id),
    INDEX idx_mistakes_session (session_id)
);

-- ------------------------------------------------------------
-- 6. Password reset codes
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS password_reset_tokens (
    id          BIGINT       PRIMARY KEY AUTO_INCREMENT,
    email       VARCHAR(100) NOT NULL,
    code        VARCHAR(6)   NOT NULL,
    expires_at  DATETIME     NOT NULL,
    used        TINYINT(1)   NOT NULL DEFAULT 0,
    created_at  DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_password_reset_email_code (email, code)
);

-- ------------------------------------------------------------
-- 7. SessionUtterance
-- Per-utterance STT transcripts within a session
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS session_utterance (
    utterance_id   BIGINT       PRIMARY KEY AUTO_INCREMENT,
    session_id     VARCHAR(36)  NOT NULL,
    speaker        VARCHAR(36),                       -- user_id or 'partner'
    raw_text       TEXT         NOT NULL,             -- STT output
    audio_url      VARCHAR(500),
    spoken_at      DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (session_id) REFERENCES sessions(session_id) ON DELETE CASCADE
);

-- ------------------------------------------------------------
-- 8. TopicPreferences
-- Topic tags tied to users and sessions
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS topic_preferences (
    topic_id       BIGINT       PRIMARY KEY AUTO_INCREMENT,
    session_id     VARCHAR(36)  NOT NULL,
    user_id        VARCHAR(36)  NOT NULL,
    domain         VARCHAR(100),
    scenario       VARCHAR(100),
    topic          VARCHAR(100),
    topic_tags     JSON,
    FOREIGN KEY (session_id) REFERENCES sessions(session_id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);

-- ------------------------------------------------------------
-- 9. RelationshipAnalysis
-- ML model output: formality, social distance, politeness
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS relationship_analysis (
    analysis_id    BIGINT       PRIMARY KEY AUTO_INCREMENT,
    session_id     VARCHAR(36)  NOT NULL,
    utterance_id   BIGINT,
    formality      VARCHAR(50),                       -- e.g. informal, mixed
    politeness     VARCHAR(50),                       -- e.g. polite, very_polite
    social_distance FLOAT,
    status_gap     FLOAT,
    ml_model_ver   VARCHAR(50),
    analyzed_at    DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (session_id) REFERENCES sessions(session_id) ON DELETE CASCADE,
    FOREIGN KEY (utterance_id) REFERENCES session_utterance(utterance_id) ON DELETE SET NULL
);

-- ------------------------------------------------------------
-- 10. SessionMistakes
-- Per-turn corrections captured during chat, used as input for analysis
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS session_mistakes (
    id           BIGINT        PRIMARY KEY AUTO_INCREMENT,
    session_id   VARCHAR(36)   NOT NULL,
    turn_number  INT           NOT NULL,
    original     TEXT          NOT NULL,
    corrected    TEXT          NOT NULL,
    error_type   VARCHAR(50)   NOT NULL,
    severity     VARCHAR(20)   NOT NULL DEFAULT 'warning',
    explanation  TEXT,
    created_at   DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_session (session_id)
);

-- ------------------------------------------------------------
-- 11. Feedback
-- LLM (HyperCLOVA X) generated feedback per session/utterance
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS feedback (
    feedback_id    BIGINT       PRIMARY KEY AUTO_INCREMENT,
    session_id     VARCHAR(36)  NOT NULL,
    utterance_id   BIGINT,
    difficulty     VARCHAR(50),
    llm_feedback   TEXT,                              -- HyperCLOVA X output
    suggestion     TEXT,
    created_at     DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (session_id) REFERENCES sessions(session_id) ON DELETE CASCADE,
    FOREIGN KEY (utterance_id) REFERENCES session_utterance(utterance_id) ON DELETE SET NULL
);
