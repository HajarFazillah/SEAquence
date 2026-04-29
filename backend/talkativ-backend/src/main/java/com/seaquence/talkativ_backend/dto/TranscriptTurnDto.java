package com.seaquence.talkativ_backend.dto;

import lombok.AllArgsConstructor;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

@Getter
@Setter
@NoArgsConstructor
@AllArgsConstructor
public class TranscriptTurnDto {
    private String id;
    private String speaker;
    private String text;
    private String type; // "final"
}