package com.seaquence.talkativ_backend.dto;

import java.util.List;

public class RegisterRequest {
    private String username;
    private String email;
    private String password;
    private String nativeLang;
    private String targetLang;
    private String koreanLevel;
    private String age;
    private String gender;
    private String memo;
    private List<String> interests;
    private List<String> dislikes;

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

    public String getAge() { return age; }
    public void setAge(String age) { this.age = age; }

    public String getGender() { return gender; }
    public void setGender(String gender) { this.gender = gender; }

    public String getMemo() { return memo; }
    public void setMemo(String memo) { this.memo = memo; }

    public List<String> getInterests() { return interests; }
    public void setInterests(List<String> interests) { this.interests = interests; }

    public List<String> getDislikes() { return dislikes; }
    public void setDislikes(List<String> dislikes) { this.dislikes = dislikes; }
}
