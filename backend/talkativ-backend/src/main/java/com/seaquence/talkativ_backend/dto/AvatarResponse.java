package com.seaquence.talkativ_backend.dto;

import com.seaquence.talkativ_backend.entity.Avatar;
import com.fasterxml.jackson.annotation.JsonProperty;
import com.fasterxml.jackson.core.type.TypeReference;
import com.fasterxml.jackson.databind.ObjectMapper;
import java.util.List;

public class AvatarResponse {

    @JsonProperty("id")                       private Long id;
    @JsonProperty("name_ko")                  private String nameKo;
    @JsonProperty("name_en")                  private String nameEn;
    @JsonProperty("avatar_type")              private String avatarType;
    @JsonProperty("age")                      private String age;
    @JsonProperty("gender")                   private String gender;
    @JsonProperty("avatar_bg")                private String avatarBg;
    @JsonProperty("icon")                     private String icon;
    @JsonProperty("role")                     private String role;
    @JsonProperty("custom_role")              private String customRole;
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

    private static final ObjectMapper mapper = new ObjectMapper();

    // Static factory — converts entity to response, deserializes JSON arrays
    public static AvatarResponse from(Avatar avatar) {
        AvatarResponse r = new AvatarResponse();
        r.id                     = avatar.getAvatarId();
        r.nameKo                 = avatar.getNameKo();
        r.nameEn                 = avatar.getNameEn();
        r.age                    = avatar.getAge();
        r.gender                 = avatar.getGender();
        r.avatarType             = avatar.getAvatarType();
        r.avatarBg               = avatar.getAvatarBg();
        r.icon                   = avatar.getIcon();
        r.role                   = avatar.getRole();
        r.customRole             = avatar.getCustomRole();
        r.relationshipDescription = avatar.getRelationshipDescription();
        r.difficulty             = avatar.getDifficulty();
        r.description            = avatar.getDescription();
        r.speakingStyle          = avatar.getSpeakingStyle();
        r.memo                   = avatar.getMemo();
        r.formalityToUser        = avatar.getFormalityToUser();
        r.formalityFromUser      = avatar.getFormalityFromUser();
        r.bio                    = avatar.getBio();
        r.personalityTraits      = parseList(avatar.getPersonalityTraits());
        r.interests              = parseList(avatar.getInterests());
        r.dislikes               = parseList(avatar.getDislikes());
        return r;
    }

    private static List<String> parseList(String json) {
        if (json == null || json.isEmpty()) return List.of();
        try {
            return mapper.readValue(json, new TypeReference<List<String>>() {});
        } catch (Exception e) {
            return List.of();
        }
    }

    // Getters
    public Long getId()                      { return id; }
    public String getNameKo()               { return nameKo; }
    public String getNameEn()               { return nameEn; }
    public String getAge()                  { return age; }
    public String getGender()               { return gender; }
    public String getAvatarType()           { return avatarType; }
    public String getAvatarBg()             { return avatarBg; }
    public String getIcon()                 { return icon; }
    public String getRole()                 { return role; }
    public String getCustomRole()           { return customRole; }
    public String getRelationshipDescription() { return relationshipDescription; }
    public String getDifficulty()           { return difficulty; }
    public String getDescription()          { return description; }
    public List<String> getPersonalityTraits() { return personalityTraits; }
    public String getSpeakingStyle()        { return speakingStyle; }
    public List<String> getInterests()      { return interests; }
    public List<String> getDislikes()       { return dislikes; }
    public String getMemo()                 { return memo; }
    public String getFormalityToUser()      { return formalityToUser; }
    public String getFormalityFromUser()    { return formalityFromUser; }
    public String getBio()                  { return bio; }
}