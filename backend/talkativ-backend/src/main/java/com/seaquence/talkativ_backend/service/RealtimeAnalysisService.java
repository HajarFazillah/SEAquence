package com.seaquence.talkativ_backend.service;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.seaquence.talkativ_backend.dto.InsightDto;
import com.seaquence.talkativ_backend.dto.RealtimeAnalysisResponse;
import com.seaquence.talkativ_backend.dto.TranscriptTurnDto;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.*;
import org.springframework.stereotype.Service;
import org.springframework.web.client.RestTemplate;
import org.springframework.web.multipart.MultipartFile;

import java.util.*;

@Service
public class RealtimeAnalysisService {

    private final ClovaSpeechService clovaSpeechService;
    private final RestTemplate restTemplate;
    private final ObjectMapper objectMapper = new ObjectMapper();

    @Value("${ai.server.url}")
    private String aiServerUrl;

    public RealtimeAnalysisService(ClovaSpeechService clovaSpeechService) {
        this.clovaSpeechService = clovaSpeechService;
        this.restTemplate = new RestTemplate();
    }

    public RealtimeAnalysisResponse analyzeRealtimeAudio(MultipartFile file, String avatarRole) {
        ClovaSpeechService.ClovaSpeechResult speechResult = clovaSpeechService.transcribeWithDiarization(file);

        List<TranscriptTurnDto> turns = new ArrayList<>();
        List<InsightDto> insights = new ArrayList<>();

        if (speechResult.getTurns() == null || speechResult.getTurns().isEmpty()) {
            return new RealtimeAnalysisResponse(turns, insights);
        }

        // First speaker label to appear = user
        String userSpeakerLabel = null;
        int idx = 1;
        for (ClovaSpeechService.SpeakerTurn turn : speechResult.getTurns()) {
            String turnId = "turn-" + idx;
            turns.add(new TranscriptTurnDto(turnId, turn.getSpeaker(), turn.getText(), "final"));
            if (userSpeakerLabel == null) userSpeakerLabel = turn.getSpeaker();
            idx++;
        }

        // Call AI server for each user turn
        for (TranscriptTurnDto turn : turns) {
            if (!turn.getSpeaker().equals(userSpeakerLabel)) continue;
            if (turn.getText() == null || turn.getText().isBlank()) continue;

            try {
                InsightDto insight = analyzeTurn(turn.getId(), turn.getText(), avatarRole);
                if (insight != null) insights.add(insight);
            } catch (Exception e) {
                System.err.println("[AI] Failed to analyze turn " + turn.getId() + ": " + e.getMessage());
            }
        }

        return new RealtimeAnalysisResponse(turns, insights);
    }

    private InsightDto analyzeTurn(String turnId, String text, String avatarRole) throws Exception {
        HttpHeaders headers = new HttpHeaders();
        headers.setContentType(MediaType.APPLICATION_JSON);

        Map<String, Object> body = new HashMap<>();
        body.put("text", text);
        body.put("user_age", 22);
        if (avatarRole != null && !avatarRole.isBlank()) {
            body.put("target_role", avatarRole);
        }

        HttpEntity<Map<String, Object>> request = new HttpEntity<>(body, headers);
        ResponseEntity<String> response = restTemplate.exchange(
                aiServerUrl + "/api/v1/analysis/politeness",
                HttpMethod.POST,
                request,
                String.class
        );

        JsonNode root = objectMapper.readTree(response.getBody());
        boolean isAppropriate = root.path("is_appropriate").asBoolean(true);

        // Skip insight when speech is appropriate — only surface real issues
        if (isAppropriate) return null;

        String feedbackKo = root.path("feedback_ko").asText("");

        // Extract first correction as a suggestion
        String suggestion = null;
        JsonNode corrections = root.path("details").path("corrections");
        if (corrections.isArray() && corrections.size() > 0) {
            JsonNode first = corrections.get(0);
            String corrected = first.path("corrected").asText("").trim();
            if (!corrected.isBlank()) {
                suggestion = corrected;
            }
        }

        String message = feedbackKo.isBlank() ? "표현을 개선해보세요." : feedbackKo;

        return new InsightDto("insight-" + turnId, "risk", message, suggestion, turnId);
    }
}
