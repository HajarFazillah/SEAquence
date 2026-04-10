package com.seaquence.talkativ_backend.dto;

public class SessionRequest {

    private String avatarId;
    private String avatarName;
    private String avatarIcon;
    private String avatarBg;
    private String situation;
    private String difficulty;

    public SessionRequest() {}

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

    public String getDifficulty() { return difficulty; }
    public void setDifficulty(String difficulty) { this.difficulty = difficulty; }
}