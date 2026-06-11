package com.seaquence.talkativ_backend.dto;

public class SessionMessageRequest {
    private String role;
    private String content;

    public String getRole() { return role; }
    public void setRole(String role) { this.role = role; }
    public String getContent() { return content; }
    public void setContent(String content) { this.content = content; }
}
