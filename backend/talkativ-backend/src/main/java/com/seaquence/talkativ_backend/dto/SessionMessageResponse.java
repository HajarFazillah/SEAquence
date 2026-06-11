package com.seaquence.talkativ_backend.dto;

public class SessionMessageResponse {
    private final int turnNumber;
    private final String role;
    private final String content;
    private final String createdAt;

    public SessionMessageResponse(int turnNumber, String role, String content, String createdAt) {
        this.turnNumber = turnNumber;
        this.role = role;
        this.content = content;
        this.createdAt = createdAt;
    }

    public int getTurnNumber() { return turnNumber; }
    public String getRole() { return role; }
    public String getContent() { return content; }
    public String getCreatedAt() { return createdAt; }
}
