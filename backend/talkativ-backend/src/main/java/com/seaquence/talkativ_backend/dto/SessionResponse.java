package com.seaquence.talkativ_backend.dto;

public class SessionResponse {
    private String sessionId;
    private String avatarId;
    private String avatarName;
    private String avatarIcon;
    private String avatarBg;
    private String situation;
    private int mood;
    private String difficulty;
    private String lastMessageAt;
    private String endedAt;

    public SessionResponse(String sessionId, String avatarId, String avatarName,
                           String avatarIcon, String avatarBg, String situation,
                           int mood, String difficulty, String lastMessageAt,
                           String endedAt) {
        this.sessionId = sessionId;
        this.avatarId = avatarId;
        this.avatarName = avatarName;
        this.avatarIcon = avatarIcon;
        this.avatarBg = avatarBg;
        this.situation = situation;
        this.mood = mood;
        this.difficulty = difficulty;
        this.lastMessageAt = lastMessageAt;
        this.endedAt = endedAt;
    }

    public String getSessionId() { return sessionId; }
    public String getAvatarId() { return avatarId; }
    public String getAvatarName() { return avatarName; }
    public String getAvatarIcon() { return avatarIcon; }
    public String getAvatarBg() { return avatarBg; }
    public String getSituation() { return situation; }
    public int getMood() { return mood; }
    public String getDifficulty() { return difficulty; }
    public String getLastMessageAt() { return lastMessageAt; }
    public String getEndedAt() { return endedAt; }
}