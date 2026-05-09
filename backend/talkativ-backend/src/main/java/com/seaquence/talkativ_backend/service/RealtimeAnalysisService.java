package com.seaquence.talkativ_backend.service;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.seaquence.talkativ_backend.dto.InsightDto;
import com.seaquence.talkativ_backend.dto.RealtimeAnalysisResponse;
import com.seaquence.talkativ_backend.dto.TranscriptTurnDto;
import com.seaquence.talkativ_backend.entity.Mistake;
import com.seaquence.talkativ_backend.repository.MistakeRepository;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.*;
import org.springframework.stereotype.Service;
import org.springframework.web.client.RestTemplate;
import org.springframework.web.multipart.MultipartFile;

import java.util.*;
import java.util.regex.Pattern;

@Service
public class RealtimeAnalysisService {

    private final ClovaSpeechService clovaSpeechService;
    private final MistakeRepository mistakeRepository;
    private final RestTemplate restTemplate;
    private final ObjectMapper objectMapper = new ObjectMapper();

    // Korean sentence terminators: . ? ! plus '다.' '요.' style endings.
    // We split on terminator + optional whitespace; keep terminator with the sentence.
    private static final Pattern SENTENCE_SPLIT = Pattern.compile("(?<=[.!?。？！])\\s+|(?<=[다요죠]\\.)\\s+");

    @Value("${ai.server.url}")
    private String aiServerUrl;

    public RealtimeAnalysisService(
            ClovaSpeechService clovaSpeechService,
            MistakeRepository mistakeRepository
    ) {
        this.clovaSpeechService = clovaSpeechService;
        this.mistakeRepository = mistakeRepository;
        this.restTemplate = new RestTemplate();
    }

    public RealtimeAnalysisResponse analyzeRealtimeAudio(
            MultipartFile file,
            String avatarRole,
            String userId,
            String sessionId,
            String expectedSpeechLevel,
            String userSpeakerHint
    ) {
        ClovaSpeechService.ClovaSpeechResult speechResult = clovaSpeechService.transcribeWithDiarization(file);

        List<TranscriptTurnDto> turns = new ArrayList<>();
        List<InsightDto> insights = new ArrayList<>();

        if (speechResult.getTurns() == null || speechResult.getTurns().isEmpty()) {
            return new RealtimeAnalysisResponse(turns, insights);
        }

        // Identify which CLOVA speaker label maps to the user.
        // Prefer explicit hint from client; fall back to "first speaker = user".
        String userSpeakerLabel = (userSpeakerHint != null && !userSpeakerHint.isBlank())
                ? userSpeakerHint
                : null;

        int idx = 1;
        for (ClovaSpeechService.SpeakerTurn turn : speechResult.getTurns()) {
            String turnId = "turn-" + idx;
            turns.add(new TranscriptTurnDto(turnId, turn.getSpeaker(), turn.getText(), "final"));
            if (userSpeakerLabel == null) userSpeakerLabel = turn.getSpeaker();
            idx++;
        }

        String resolvedSpeechLevel = (expectedSpeechLevel == null || expectedSpeechLevel.isBlank())
                ? "polite"
                : expectedSpeechLevel;

        int turnNumber = 0;
        for (TranscriptTurnDto turn : turns) {
            if (!turn.getSpeaker().equals(userSpeakerLabel)) continue;
            if (turn.getText() == null || turn.getText().isBlank()) continue;

            turnNumber++;
            for (String sentence : splitSentences(turn.getText())) {
                if (sentence.isBlank()) continue;
                try {
                    List<CorrectionItem> corrections = analyzeSentence(
                            sentence, avatarRole, resolvedSpeechLevel
                    );
                    for (CorrectionItem c : corrections) {
                        insights.add(new InsightDto(
                                "insight-" + turn.getId() + "-" + insights.size(),
                                "error".equalsIgnoreCase(c.severity) ? "risk" : "risk",
                                c.explanation != null && !c.explanation.isBlank()
                                        ? c.explanation
                                        : "표현을 다듬어보세요.",
                                c.corrected,
                                turn.getId()
                        ));
                        persistMistake(userId, sessionId, turnNumber, c);
                    }
                } catch (Exception e) {
                    System.err.println("[Realtime] analyze sentence failed: " + e.getMessage());
                }
            }
        }

        return new RealtimeAnalysisResponse(turns, insights);
    }

    private List<String> splitSentences(String text) {
        if (text == null || text.isBlank()) return Collections.emptyList();
        String[] parts = SENTENCE_SPLIT.split(text.trim());
        List<String> out = new ArrayList<>();
        for (String p : parts) {
            String trimmed = p.trim();
            if (!trimmed.isEmpty()) out.add(trimmed);
        }
        return out;
    }

    private List<CorrectionItem> analyzeSentence(String sentence, String avatarRole, String expectedSpeechLevel) throws Exception {
        HttpHeaders headers = new HttpHeaders();
        headers.setContentType(MediaType.APPLICATION_JSON);

        Map<String, Object> body = new HashMap<>();
        body.put("message", sentence);
        body.put("expected_speech_level", expectedSpeechLevel);
        if (avatarRole != null && !avatarRole.isBlank()) {
            body.put("avatar_role", avatarRole);
        }
        body.put("user_level", "intermediate");

        HttpEntity<Map<String, Object>> request = new HttpEntity<>(body, headers);
        ResponseEntity<String> response = restTemplate.exchange(
                aiServerUrl + "/api/v1/chat/check",
                HttpMethod.POST,
                request,
                String.class
        );

        JsonNode root = objectMapper.readTree(response.getBody());
        if (!root.path("has_errors").asBoolean(false)) return Collections.emptyList();

        List<CorrectionItem> out = new ArrayList<>();
        JsonNode corrections = root.path("corrections");
        if (corrections.isArray()) {
            for (JsonNode c : corrections) {
                CorrectionItem item = new CorrectionItem();
                item.original = c.path("original").asText("");
                item.corrected = c.path("corrected").asText("");
                item.type = c.path("type").asText("grammar");
                item.severity = c.path("severity").asText("warning");
                item.explanation = c.path("explanation").asText("");
                item.tip = c.path("tip").asText(null);
                if (!item.original.isBlank() && !item.corrected.isBlank()) {
                    out.add(item);
                }
            }
        }
        return out;
    }

    private void persistMistake(String userId, String sessionId, int turnNumber, CorrectionItem c) {
        if (sessionId == null || sessionId.isBlank()) return;
        // Only save real issues, not info-level suggestions.
        if (!"error".equalsIgnoreCase(c.severity) && !"warning".equalsIgnoreCase(c.severity)) return;
        try {
            Mistake m = new Mistake();
            m.setSessionId(sessionId);
            m.setUserId(userId == null || userId.isBlank() ? "anonymous" : userId);
            m.setTurnNumber(turnNumber);
            m.setOriginalText(c.original);
            m.setCorrectedText(c.corrected);
            m.setCorrectionType(c.type);
            m.setSeverity(c.severity);
            m.setExplanation(c.explanation);
            m.setTip(c.tip);
            mistakeRepository.save(m);
        } catch (Exception e) {
            System.err.println("[Realtime] persist mistake failed: " + e.getMessage());
        }
    }

    private static class CorrectionItem {
        String original;
        String corrected;
        String type;
        String severity;
        String explanation;
        String tip;
    }
}
