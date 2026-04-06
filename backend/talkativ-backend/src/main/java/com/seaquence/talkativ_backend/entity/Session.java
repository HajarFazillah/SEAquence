package com.seaquence.talkativ_backend.entity;

import jakarta.persistence.*;
import org.hibernate.annotations.CreationTimestamp;
import java.time.LocalDateTime;

@Entity
@Table(name = "sessions")
public class Session {

    @Id
    @Column(name = "session_id", length = 36)
    private String sessionId;

    @Column(name = "user_id", nullable = false, length = 36)
    private String userId;

    @Column(name = "avatar_id", nullable = false, length = 100)
    private String avatarId;

    @Column(name = "avatar_name", nullable = false, length = 100)
    private String avatarName;

    @Column(name = "avatar_icon", nullable = false, length = 50)
    private String avatarIcon;

    @Column(name = "avatar_bg", nullable = false, length = 20)
    private String avatarBg;

    @Column(nullable = false, length = 200)
    private String situation;

    @Column(nullable = false)
    private int mood = 50;

    @Column(nullable = false, length = 20)
    private String difficulty = "medium";

    @Column(nullable = false, length = 20)
    private String status = "active";

    @CreationTimestamp
    @Column(name = "started_at", updatable = false)
    private LocalDateTime startedAt;

    @Column(name = "ended_at")
    private LocalDateTime endedAt;

    // Getters and Setters
    public String getSessionId() { return sessionId; }
    public void setSessionId(String sessionId) { this.sessionId = sessionId; }

    public String getUserId() { return userId; }
    public void setUserId(String userId) { this.userId = userId; }

    public String getAvatarId() { return avatarId; }
    public void setAvatarId(String avatarId) { this.avatarId = avatarId; }

    public String getAvatarName() { return avatarName; }
    public void setAvatarName(String avatarName) { this.avatarName = avatarName; }

    public String getAvatarIcon() { return avatarIcon; }
    public void setAvatarIcon(String avatarIcon) { this.avatarIcon = avatarIcon; }

    public String getAvatarBg() { return avatarBg; }
    public void setAvatarBg(String avatarBg) { this.avatarBg = avatarBg; }

    public String getSituation() { return situation; }
    public void setSituation(String situation) { this.situation = situation; }

    public int getMood() { return mood; }
    public void setMood(int mood) { this.mood = mood; }

    public String getDifficulty() { return difficulty; }
    public void setDifficulty(String difficulty) { this.difficulty = difficulty; }

    public String getStatus() { return status; }
    public void setStatus(String status) { this.status = status; }

    public LocalDateTime getStartedAt() { return startedAt; }
    public LocalDateTime getEndedAt() { return endedAt; }
    public void setEndedAt(LocalDateTime endedAt) { this.endedAt = endedAt; }
}