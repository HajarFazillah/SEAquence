package com.seaquence.talkativ_backend.dto;

import lombok.AllArgsConstructor;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

import java.util.List;

@Getter
@Setter
@NoArgsConstructor
@AllArgsConstructor
public class TranscriptTurnDto {
    private String id;
    private String speaker;
    private String text;
    private String type; // "final"
    private List<String> suggestions; // response suggestions for partner turns; null for user turns
}