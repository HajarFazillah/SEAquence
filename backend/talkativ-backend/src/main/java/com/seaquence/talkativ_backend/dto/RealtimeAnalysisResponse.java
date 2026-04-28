package com.seaquence.talkativ_backend.dto;

import java.util.List;

import lombok.AllArgsConstructor;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

@Getter
@Setter
@NoArgsConstructor
@AllArgsConstructor
public class RealtimeAnalysisResponse {
    private List<TranscriptTurnDto> turns;
    private List<InsightDto> insights;
}