package com.seaquence.talkativ_backend.dto;

public class AvatarResponse {
    private Long avatarId;
    private String userId;
    private String imageUrl;
    private String style;
    private Boolean isActive;

    public AvatarResponse(Long avatarId, String userId, String imageUrl,
                          String style, Boolean isActive) {
        this.avatarId = avatarId;
        this.userId = userId;
        this.imageUrl = imageUrl;
        this.style = style;
        this.isActive = isActive;
    }

    public Long getAvatarId() { return avatarId; }
    public String getUserId() { return userId; }
    public String getImageUrl() { return imageUrl; }
    public String getStyle() { return style; }
    public Boolean getIsActive() { return isActive; }
}
