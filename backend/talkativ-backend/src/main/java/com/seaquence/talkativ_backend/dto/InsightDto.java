package com.seaquence.talkativ_backend.dto;

import lombok.AllArgsConstructor;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

@Getter
@Setter
@NoArgsConstructor
@AllArgsConstructor
public class InsightDto {
    private String id;
    private String kind; // "risk" | "success"
    private String message;
    private String suggestion;
    private String turnId;
}