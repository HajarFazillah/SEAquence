package com.seaquence.talkativ_backend.controller;

import com.seaquence.talkativ_backend.dto.SessionResponse;
import com.seaquence.talkativ_backend.entity.Session;
import com.seaquence.talkativ_backend.repository.SessionRepository;
import org.springframework.http.ResponseEntity;
import org.springframework.security.core.Authentication;
import org.springframework.web.bind.annotation.*;

import java.util.List;
import java.util.stream.Collectors;

@RestController
@RequestMapping("/api/sessions")
@CrossOrigin(origins = "*")
public class SessionController {

    private final SessionRepository sessionRepository;

    public SessionController(SessionRepository sessionRepository) {
        this.sessionRepository = sessionRepository;
    }

    @GetMapping
    public ResponseEntity<List<SessionResponse>> getSessions(
            @RequestParam(defaultValue = "active") String status,
            Authentication auth) {
        String userId = (String) auth.getPrincipal();
        List<Session> sessions = sessionRepository.findByUserIdAndStatus(userId, status);
        List<SessionResponse> response = sessions.stream()
                .map(s -> new SessionResponse(
                        s.getSessionId(), s.getAvatarId(), s.getAvatarName(),
                        s.getAvatarIcon(), s.getAvatarBg(), s.getSituation(),
                        s.getMood(), s.getDifficulty(),
                        s.getStartedAt() != null ? s.getStartedAt().toString() : null))
                .collect(Collectors.toList());
        return ResponseEntity.ok(response);
    }
}