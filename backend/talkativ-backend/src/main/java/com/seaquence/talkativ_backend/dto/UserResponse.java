package com.seaquence.talkativ_backend.dto;

public class UserResponse {
    private String userId;
    private String username;
    private String email;
    private String nativeLang;
    private String targetLang;
    private String koreanLevel;
    private String provider;

    public UserResponse(String userId, String username, String email,
                        String nativeLang, String targetLang,
                        String koreanLevel, String provider) {
        this.userId = userId;
        this.username = username;
        this.email = email;
        this.nativeLang = nativeLang;
        this.targetLang = targetLang;
        this.koreanLevel = koreanLevel;
        this.provider = provider;
    }

    public String getUserId() { return userId; }
    public String getUsername() { return username; }
    public String getEmail() { return email; }
    public String getNativeLang() { return nativeLang; }
    public String getTargetLang() { return targetLang; }
    public String getKoreanLevel() { return koreanLevel; }
    public String getProvider() { return provider; }
}
