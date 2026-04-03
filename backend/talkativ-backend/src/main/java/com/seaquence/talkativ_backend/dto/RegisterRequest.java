package com.seaquence.talkativ_backend.dto;

public class RegisterRequest {
    private String username;
    private String email;
    private String password;
    private String nativeLang;
    private String targetLang;
    private String koreanLevel;

    public String getUsername() { return username; }
    public void setUsername(String username) { this.username = username; }

    public String getEmail() { return email; }
    public void setEmail(String email) { this.email = email; }

    public String getPassword() { return password; }
    public void setPassword(String password) { this.password = password; }

    public String getNativeLang() { return nativeLang; }
    public void setNativeLang(String nativeLang) { this.nativeLang = nativeLang; }

    public String getTargetLang() { return targetLang; }
    public void setTargetLang(String targetLang) { this.targetLang = targetLang; }

    public String getKoreanLevel() { return koreanLevel; }
    public void setKoreanLevel(String koreanLevel) { this.koreanLevel = koreanLevel; }
}
