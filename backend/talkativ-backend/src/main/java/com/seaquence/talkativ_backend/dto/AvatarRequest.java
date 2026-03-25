package com.seaquence.talkativ_backend.dto;

public class AvatarRequest {
    private String imageUrl;
    private String style;

    public String getImageUrl() { return imageUrl; }
    public void setImageUrl(String imageUrl) { this.imageUrl = imageUrl; }

    public String getStyle() { return style; }
    public void setStyle(String style) { this.style = style; }
}
