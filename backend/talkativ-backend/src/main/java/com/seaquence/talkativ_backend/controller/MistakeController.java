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

        Map<String, int[]> counters = new HashMap<>();
        for (Mistake m : mistakes) {
            String type = m.getCorrectionType() != null ? m.getCorrectionType() : "other";
            int[] entry = counters.computeIfAbsent(type, k -> new int[]{0, 0, 0}); // total, error, warning
            entry[0]++;
            if ("error".equalsIgnoreCase(m.getSeverity())) entry[1]++;
            else if ("warning".equalsIgnoreCase(m.getSeverity())) entry[2]++;
        }

        List<Map<String, Object>> result = new ArrayList<>();
        counters.forEach((type, c) -> {
            Map<String, Object> row = new HashMap<>();
            row.put("error_type", type);
            row.put("error_type_ko", toKoreanLabel(type));
            row.put("count", c[0]);
            row.put("severity", c[1] > c[2] ? "high" : (c[2] > 0 ? "medium" : "low"));
            result.add(row);
        });
        result.sort((a, b) -> Integer.compare((int) b.get("count"), (int) a.get("count")));
        return ResponseEntity.ok(result);
    }

    private String toKoreanLabel(String type) {
        switch (type == null ? "" : type.toLowerCase()) {
            case "grammar":      return "문법";
            case "spelling":     return "맞춤법";
            case "vocabulary":   return "어휘";
            case "word_choice":  return "단어 선택";
            case "speech_level": return "존댓말";
            case "honorific":    return "존댓말";
            case "naturalness":  return "자연스러움";
            default:             return "기타";
        }
    }
}
