package com.seaquence.talkativ_backend.entity;

import java.time.LocalDateTime;

import org.hibernate.annotations.CreationTimestamp;
import org.hibernate.annotations.UpdateTimestamp;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.Id;
import jakarta.persistence.Table;

@Entity
@Table(name = "users")
public class User {

    @Id
    @Column(name = "user_id", length = 36)
    private String userId;

    @Column(nullable = false, unique = true, length = 50)
    private String username;

    @Column(nullable = false, unique = true, length = 100)
    private String email;

    @Column(length = 255)
    private String password;

    @Column(length = 10)
    private String provider = "local";

    @Column(name = "avatar_url", length = 500)
    private String avatarUrl;

    @Column(name = "native_lang", length = 10)
    private String nativeLang;

    @Column(name = "target_lang", length = 10)
    private String targetLang;

    @Column(name = "korean_level", length = 20)
    private String koreanLevel = "intermediate";

    @Column(name = "privacy_consent")
    private Boolean privacyConsent = false;

    @CreationTimestamp
    @Column(name = "created_at", updatable = false)
    private LocalDateTime createdAt;

    @UpdateTimestamp
    @Column(name = "updated_at")
    private LocalDateTime updatedAt;

    // Getters and Setters
    public String getUserId() { return userId; }
    public void setUserId(String userId) { this.userId = userId; }

    public String getUsername() { return username; }
    public void setUsername(String username) { this.username = username; }

    public String getEmail() { return email; }
    public void setEmail(String email) { this.email = email; }

    public String getPassword() { return password; }
    public void setPassword(String password) { this.password = password; }

    public String getProvider() { return provider; }
    public void setProvider(String provider) { this.provider = provider; }

    public String getNativeLang() { return nativeLang; }
    public void setNativeLang(String nativeLang) { this.nativeLang = nativeLang; }

    public String getTargetLang() { return targetLang; }
    public void setTargetLang(String targetLang) { this.targetLang = targetLang; }

    public String getKoreanLevel() { return koreanLevel; }
    public void setKoreanLevel(String koreanLevel) { this.koreanLevel = koreanLevel; }

    public Boolean getPrivacyConsent() { return privacyConsent; }
    public void setPrivacyConsent(Boolean privacyConsent) { this.privacyConsent = privacyConsent; }

    public LocalDateTime getCreatedAt() { return createdAt; }
    public LocalDateTime getUpdatedAt() { return updatedAt; }

    public String getAvatarUrl() { return avatarUrl; }
    public void setAvatarUrl(String avatarUrl) { this.avatarUrl = avatarUrl; }
}
