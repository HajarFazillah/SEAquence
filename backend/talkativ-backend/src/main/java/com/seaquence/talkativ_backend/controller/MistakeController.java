package com.seaquence.talkativ_backend.controller;

import com.seaquence.talkativ_backend.dto.MistakeRequest;
import com.seaquence.talkativ_backend.entity.Mistake;
import com.seaquence.talkativ_backend.repository.MistakeRepository;
import org.springframework.http.ResponseEntity;
import org.springframework.security.core.Authentication;
import org.springframework.web.bind.annotation.*;

import java.util.ArrayList;
import java.util.Comparator;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

@RestController
@RequestMapping(value = "/api/mistakes", produces = "application/json;charset=UTF-8")
@CrossOrigin(origins = "*")
public class MistakeController {

    private final MistakeRepository mistakeRepository;

    public MistakeController(MistakeRepository mistakeRepository) {
        this.mistakeRepository = mistakeRepository;
    }

    // Save mistakes after each chat turn
    @PostMapping
    public ResponseEntity<Void> saveMistakes(
            @RequestBody MistakeRequest request,
            Authentication auth) {

        String userId = (auth != null && auth.getPrincipal() != null)
                ? (String) auth.getPrincipal()
                : "anonymous";

        if (request.getMistakes() == null || request.getMistakes().isEmpty()) {
            return ResponseEntity.ok().build();
        }

        for (MistakeRequest.MistakeItem item : request.getMistakes()) {
            Mistake mistake = new Mistake();
            mistake.setSessionId(request.getSessionId());
            mistake.setUserId(userId);
            mistake.setTurnNumber(request.getTurnNumber());
            mistake.setOriginalText(item.getOriginalText());
            mistake.setCorrectedText(item.getCorrectedText());
            mistake.setCorrectionType(item.getCorrectionType());
            mistake.setSeverity(item.getSeverity());
            mistake.setExplanation(item.getExplanation());
            mistake.setTip(item.getTip());
            mistakeRepository.save(mistake);
        }

        return ResponseEntity.ok().build();
    }

    // Get all mistakes for a specific session
    @GetMapping("/session/{sessionId}")
    public ResponseEntity<List<Mistake>> getMistakesBySession(
            @PathVariable String sessionId,
            Authentication auth) {

        List<Mistake> mistakes = mistakeRepository
                .findBySessionIdOrderByTurnNumberAsc(sessionId);
        return ResponseEntity.ok(mistakes);
    }

    // Get all mistakes for the current user
    @GetMapping("/me")
    public ResponseEntity<List<Mistake>> getMyMistakes(Authentication auth) {
        String userId = (auth != null && auth.getPrincipal() != null)
                ? (String) auth.getPrincipal()
                : "anonymous";

        List<Mistake> mistakes = mistakeRepository
                .findByUserIdOrderByCreatedAtDesc(userId);
        return ResponseEntity.ok(mistakes);
    }

    // Aggregated weak areas (for "실수 분석" page)
    @GetMapping("/me/weak-areas")
    public ResponseEntity<List<Map<String, Object>>> getMyWeakAreas(Authentication auth) {
        String userId = (auth != null && auth.getPrincipal() != null)
                ? (String) auth.getPrincipal()
                : "anonymous";

        List<Mistake> mistakes = mistakeRepository.findByUserIdOrderByCreatedAtDesc(userId);

        Map<String, WeakAreaCounter> counters = new HashMap<>();
        for (Mistake m : mistakes) {
            String rawType = m.getCorrectionType() != null ? m.getCorrectionType() : "other";
            String type = canonicalWeakAreaType(rawType);
            WeakAreaCounter entry = counters.computeIfAbsent(type, k -> new WeakAreaCounter());
            entry.total++;
            entry.weightedScore += severityWeight(m.getSeverity());
            if (!entry.rawTypes.contains(rawType)) {
                entry.rawTypes.add(rawType);
            }

            if ("error".equalsIgnoreCase(m.getSeverity()) || "high".equalsIgnoreCase(m.getSeverity())) {
                entry.error++;
            } else if ("warning".equalsIgnoreCase(m.getSeverity()) || "medium".equalsIgnoreCase(m.getSeverity())) {
                entry.warning++;
            }
        }

        List<Map<String, Object>> result = new ArrayList<>();
        counters.forEach((type, c) -> {
            Map<String, Object> row = new HashMap<>();
            row.put("error_type", type);
            row.put("error_type_ko", toKoreanLabel(type));
            row.put("count", c.total);
            row.put("weighted_score", c.weightedScore);
            row.put("types", new ArrayList<>(c.rawTypes));
            row.put("severity", c.error > c.warning ? "high" : (c.warning > 0 ? "medium" : "low"));
            result.add(row);
        });
        result.sort((a, b) -> Integer.compare((int) b.get("weighted_score"), (int) a.get("weighted_score")));
        return ResponseEntity.ok(result);
    }

    private static class WeakAreaCounter {
        int total = 0;
        int error = 0;
        int warning = 0;
        int weightedScore = 0;
        List<String> rawTypes = new ArrayList<>();
    }

    private int severityWeight(String severity) {
        if ("error".equalsIgnoreCase(severity) || "high".equalsIgnoreCase(severity)) return 3;
        if ("warning".equalsIgnoreCase(severity) || "medium".equalsIgnoreCase(severity)) return 2;
        return 1;
    }

    private String canonicalWeakAreaType(String type) {
        switch (type == null ? "" : type.toLowerCase()) {
            case "speech_level":
            case "honorific":
            case "honorifics":
            case "politeness":
            case "formality":
                return "politeness";
            case "grammar":
            case "particle":
            case "particles":
            case "ending":
            case "sentence_ending":
            case "verb_conjugation":
            case "word_order":
            case "tense":
                return "grammar";
            case "vocabulary":
            case "word_choice":
            case "expression":
                return "expression";
            case "spelling":
            case "spacing":
                return "spelling";
            case "naturalness":
            case "context":
            case "register":
                return "naturalness";
            default:
                return "other";
        }
    }

    private String toKoreanLabel(String type) {
        switch (type == null ? "" : type.toLowerCase()) {
            case "politeness":  return "존댓말/공손성";
            case "grammar":     return "문법 구조";
            case "expression":  return "표현/어휘";
            case "spelling":    return "표기";
            case "naturalness": return "자연스러움";
            default:            return "기타";
        }
    }
}
