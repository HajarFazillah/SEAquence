package com.seaquence.talkativ_backend.entity;

import jakarta.persistence.*;
import org.hibernate.annotations.CreationTimestamp;
import org.hibernate.annotations.UpdateTimestamp;
import java.time.LocalDateTime;

@Entity
@Table(name = "user_avatar")
public class Avatar {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    @Column(name = "avatar_id")
    private Long avatarId;

    @Column(name = "user_id", nullable = false, length = 36)
    private String userId;

    // ── Basic Info ───────────────────────────────────────
    @Column(name = "name_ko", nullable = true, length = 50)
    private String nameKo;

    @Column(name = "name_en", length = 50)
    private String nameEn;

    @Column(length = 10)
    private String age;

    @Column(length = 10)
    private String gender;

    @Column(name = "avatar_type", length = 20)
    private String avatarType; // "fictional" | "real"

    @Column(name = "avatar_bg", length = 20)
    private String avatarBg;

    @Column(length = 30)
    private String icon;

    // ── Relationship ─────────────────────────────────────
    @Column(length = 50)
    private String role;

    @Column(name = "custom_role", length = 50)
    private String customRole;

    @Column(name = "relationship_description", columnDefinition = "TEXT")
    private String relationshipDescription;

    @Column(length = 20)
    private String difficulty; // "easy" | "medium" | "hard"

    // ── AI Prompt Fields ─────────────────────────────────
    @Column(columnDefinition = "TEXT")
    private String description;

    // Arrays stored as JSON strings e.g. ["친절한","유쾌한"]
    @Column(name = "personality_traits", columnDefinition = "TEXT")
    private String personalityTraits;

    @Column(name = "speaking_style", columnDefinition = "TEXT")
    private String speakingStyle;

    @Column(columnDefinition = "TEXT")
    private String interests;

    @Column(columnDefinition = "TEXT")
    private String dislikes;

    @Column(columnDefinition = "TEXT")
    private String memo;

    // ── Speech Settings ──────────────────────────────────
    @Column(name = "formality_to_user", length = 20)
    private String formalityToUser;

    @Column(name = "formality_from_user", length = 20)
    private String formalityFromUser;

    @Column(columnDefinition = "TEXT")
    private String bio;

    // ── Meta ─────────────────────────────────────────────
    @Column(name = "is_active")
    private Boolean isActive = true;

    @CreationTimestamp
    @Column(name = "created_at", updatable = false)
    private LocalDateTime createdAt;

    @UpdateTimestamp
    @Column(name = "updated_at")
    private LocalDateTime updatedAt;

    // ── Getters & Setters ────────────────────────────────
    public Long getAvatarId() { return avatarId; }
    public void setAvatarId(Long avatarId) { this.avatarId = avatarId; }

    public String getUserId() { return userId; }
    public void setUserId(String userId) { this.userId = userId; }

    public String getNameKo() { return nameKo; }
    public void setNameKo(String nameKo) { this.nameKo = nameKo; }

    public String getNameEn() { return nameEn; }
    public void setNameEn(String nameEn) { this.nameEn = nameEn; }

    public String getAge() { return age; }
    public void setAge(String age) { this.age = age; }

    public String getGender() { return gender; }
    public void setGender(String gender) { this.gender = gender; }

    public String getAvatarType() { return avatarType; }
    public void setAvatarType(String avatarType) { this.avatarType = avatarType; }

    public String getAvatarBg() { return avatarBg; }
    public void setAvatarBg(String avatarBg) { this.avatarBg = avatarBg; }

    public String getIcon() { return icon; }
    public void setIcon(String icon) { this.icon = icon; }

    public String getRole() { return role; }
    public void setRole(String role) { this.role = role; }

    public String getCustomRole() { return customRole; }
    public void setCustomRole(String customRole) { this.customRole = customRole; }

    public String getRelationshipDescription() { return relationshipDescription; }
    public void setRelationshipDescription(String relationshipDescription) { this.relationshipDescription = relationshipDescription; }

    public String getDifficulty() { return difficulty; }
    public void setDifficulty(String difficulty) { this.difficulty = difficulty; }

    public String getDescription() { return description; }
    public void setDescription(String description) { this.description = description; }

    public String getPersonalityTraits() { return personalityTraits; }
    public void setPersonalityTraits(String personalityTraits) { this.personalityTraits = personalityTraits; }

    public String getSpeakingStyle() { return speakingStyle; }
    public void setSpeakingStyle(String speakingStyle) { this.speakingStyle = speakingStyle; }

    public String getInterests() { return interests; }
    public void setInterests(String interests) { this.interests = interests; }

    public String getDislikes() { return dislikes; }
    public void setDislikes(String dislikes) { this.dislikes = dislikes; }

    public String getMemo() { return memo; }
    public void setMemo(String memo) { this.memo = memo; }

    public String getFormalityToUser() { return formalityToUser; }
    public void setFormalityToUser(String formalityToUser) { this.formalityToUser = formalityToUser; }

    public String getFormalityFromUser() { return formalityFromUser; }
    public void setFormalityFromUser(String formalityFromUser) { this.formalityFromUser = formalityFromUser; }

    public String getBio() { return bio; }
    public void setBio(String bio) { this.bio = bio; }

    public Boolean getIsActive() { return isActive; }
    public void setIsActive(Boolean isActive) { this.isActive = isActive; }

    public LocalDateTime getCreatedAt() { return createdAt; }
    public LocalDateTime getUpdatedAt() { return updatedAt; }
}