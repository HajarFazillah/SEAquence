-- MySQL initialization script for Talkativ application
-- This script creates the necessary database and tables for storing user profiles, conversation sessions, utterances, topic preferences, relationship analysis results, and feedback.

CREATE DATABASE IF NOT EXISTS talkativ;
USE talkativ;

-- ------------------------------------------------------------
-- 1. UserAvatar
-- Stores user identity, profile, and privacy consent
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS user_avatar (
    user_id        VARCHAR(36)  PRIMARY KEY,          -- UUID
    username       VARCHAR(100) NOT NULL,
    email          VARCHAR(255) NOT NULL UNIQUE,
    native_lang    VARCHAR(50),
    topik_level    INT,                               -- 1–6
    privacy_consent TINYINT(1)  NOT NULL DEFAULT 0,
    created_at     DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at     DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- ------------------------------------------------------------
-- 2. Session
-- A single real-time conversation session
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS session (
    session_id     VARCHAR(36)  PRIMARY KEY,          -- UUID
    user_id        VARCHAR(36)  NOT NULL,
    started_at     DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    ended_at       DATETIME,
    FOREIGN KEY (user_id) REFERENCES user_avatar(user_id) ON DELETE CASCADE
);

-- ------------------------------------------------------------
-- 3. SessionUtterance
-- Per-utterance STT transcripts within a session
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS session_utterance (
    utterance_id   BIGINT       PRIMARY KEY AUTO_INCREMENT,
    session_id     VARCHAR(36)  NOT NULL,
    speaker        VARCHAR(36),                       -- user_id or 'partner'
    raw_text       TEXT         NOT NULL,             -- STT output
    audio_url      VARCHAR(500),
    spoken_at      DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (session_id) REFERENCES session(session_id) ON DELETE CASCADE
);

-- ------------------------------------------------------------
-- 4. TopicPreferences
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
    FOREIGN KEY (session_id) REFERENCES session(session_id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES user_avatar(user_id) ON DELETE CASCADE
);

-- ------------------------------------------------------------
-- 5. RelationshipAnalysis
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
    FOREIGN KEY (session_id) REFERENCES session(session_id) ON DELETE CASCADE,
    FOREIGN KEY (utterance_id) REFERENCES session_utterance(utterance_id) ON DELETE SET NULL
);

-- ------------------------------------------------------------
-- 6. Feedback
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
    FOREIGN KEY (session_id) REFERENCES session(session_id) ON DELETE CASCADE,
    FOREIGN KEY (utterance_id) REFERENCES session_utterance(utterance_id) ON DELETE SET NULL
);
