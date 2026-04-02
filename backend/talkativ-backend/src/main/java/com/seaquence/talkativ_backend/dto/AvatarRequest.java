package com.seaquence.talkativ_backend.dto;

import com.fasterxml.jackson.annotation.JsonProperty;
import java.util.List;

public class AvatarRequest {

    @JsonProperty("name_ko")                  private String nameKo;
    @JsonProperty("name_en")                  private String nameEn;
    @JsonProperty("age")                      private String age;
    @JsonProperty("gender")                   private String gender;
    @JsonProperty("avatarType")               private String avatarType;
    @JsonProperty("avatarBg")                 private String avatarBg;
    @JsonProperty("icon")                     private String icon;
    @JsonProperty("role")                     private String role;
    @JsonProperty("customRole")               private String customRole;
    @JsonProperty("relationship_description") private String relationshipDescription;
    @JsonProperty("difficulty")               private String difficulty;
    @JsonProperty("description")              private String description;
    @JsonProperty("personality_traits")       private List<String> personalityTraits;
    @JsonProperty("speaking_style")           private String speakingStyle;
    @JsonProperty("interests")                private List<String> interests;
    @JsonProperty("dislikes")                 private List<String> dislikes;
    @JsonProperty("memo")                     private String memo;
    @JsonProperty("formality_to_user")        private String formalityToUser;
    @JsonProperty("formality_from_user")      private String formalityFromUser;
    @JsonProperty("bio")                      private String bio;

    // Getters & Setters — ALL UNCHANGED
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
    public void setRelationshipDescription(String r) { this.relationshipDescription = r; }
    public String getDifficulty() { return difficulty; }
    public void setDifficulty(String difficulty) { this.difficulty = difficulty; }
    public String getDescription() { return description; }
    public void setDescription(String description) { this.description = description; }
    public List<String> getPersonalityTraits() { return personalityTraits; }
    public void setPersonalityTraits(List<String> personalityTraits) { this.personalityTraits = personalityTraits; }
    public String getSpeakingStyle() { return speakingStyle; }
    public void setSpeakingStyle(String speakingStyle) { this.speakingStyle = speakingStyle; }
    public List<String> getInterests() { return interests; }
    public void setInterests(List<String> interests) { this.interests = interests; }
    public List<String> getDislikes() { return dislikes; }
    public void setDislikes(List<String> dislikes) { this.dislikes = dislikes; }
    public String getMemo() { return memo; }
    public void setMemo(String memo) { this.memo = memo; }
    public String getFormalityToUser() { return formalityToUser; }
    public void setFormalityToUser(String formalityToUser) { this.formalityToUser = formalityToUser; }
    public String getFormalityFromUser() { return formalityFromUser; }
    public void setFormalityFromUser(String formalityFromUser) { this.formalityFromUser = formalityFromUser; }
    public String getBio() { return bio; }
    public void setBio(String bio) { this.bio = bio; }
}