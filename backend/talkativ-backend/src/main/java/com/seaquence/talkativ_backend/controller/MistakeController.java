package com.seaquence.talkativ_backend.controller;

import com.seaquence.talkativ_backend.dto.MistakeRequest;
import com.seaquence.talkativ_backend.entity.Mistake;
import com.seaquence.talkativ_backend.repository.MistakeRepository;
import org.springframework.http.ResponseEntity;
import org.springframework.security.core.Authentication;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@RestController
@RequestMapping("/api/mistakes")
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
}
