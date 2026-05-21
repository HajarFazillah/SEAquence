package com.seaquence.talkativ_backend.dto;

import java.util.List;

public class UserResponse {
    private String userId;
    private String username;
    private String email;
    private String nativeLang;
    private String targetLang;
    private String koreanLevel;
    private String provider;
    private String avatarUrl;
    private String age;
    private String gender;
    private String memo;
    private List<String> interests;
    private List<String> dislikes;

    public UserResponse(String userId, String username, String email,
                        String nativeLang, String targetLang,
                        String koreanLevel, String provider, String avatarUrl,
                        String age, String gender, String memo,
                        List<String> interests, List<String> dislikes) {
        this.userId = userId;
        this.username = username;
        this.email = email;
        this.nativeLang = nativeLang;
        this.targetLang = targetLang;
        this.koreanLevel = koreanLevel;
        this.provider = provider;
        this.avatarUrl = avatarUrl;
        this.age = age;
        this.gender = gender;
        this.memo = memo;
        this.interests = interests;
        this.dislikes = dislikes;
    }

    public String getUserId() { return userId; }
    public String getUsername() { return username; }
    public String getEmail() { return email; }
    public String getNativeLang() { return nativeLang; }
    public String getTargetLang() { return targetLang; }
    public String getKoreanLevel() { return koreanLevel; }
    public String getProvider() { return provider; }
    public String getAvatarUrl() { return avatarUrl; }
    public String getAge() { return age; }
    public String getGender() { return gender; }
    public String getMemo() { return memo; }
    public List<String> getInterests() { return interests; }
    public List<String> getDislikes() { return dislikes; }
}
