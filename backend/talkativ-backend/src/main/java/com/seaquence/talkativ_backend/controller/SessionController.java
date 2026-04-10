package com.seaquence.talkativ_backend.controller;

import com.seaquence.talkativ_backend.dto.SessionRequest;
import com.seaquence.talkativ_backend.dto.SessionResponse;
import com.seaquence.talkativ_backend.entity.Session;
import com.seaquence.talkativ_backend.repository.SessionRepository;
import org.springframework.http.ResponseEntity;
import org.springframework.security.core.Authentication;
import org.springframework.web.bind.annotation.*;

import java.time.LocalDateTime;
import java.util.List;
import java.util.UUID;
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

    @PostMapping
    public ResponseEntity<SessionResponse> createSession(
            @RequestBody SessionRequest request,
            Authentication auth) {

        String userId = (String) auth.getPrincipal();

        Session session = new Session();
        session.setSessionId(UUID.randomUUID().toString());
        session.setUserId(userId);
        session.setAvatarId(request.getAvatarId());
        session.setAvatarName(request.getAvatarName());
        session.setAvatarIcon(request.getAvatarIcon());
        session.setAvatarBg(request.getAvatarBg());
        session.setSituation(request.getSituation() != null ? request.getSituation() : "일상 대화");
        session.setDifficulty(request.getDifficulty() != null ? request.getDifficulty() : "medium");
        session.setMood(50);
        session.setStatus("active");

        sessionRepository.save(session);

        SessionResponse response = new SessionResponse(
                session.getSessionId(), session.getAvatarId(), session.getAvatarName(),
                session.getAvatarIcon(), session.getAvatarBg(), session.getSituation(),
                session.getMood(), session.getDifficulty(),
                session.getStartedAt() != null ? session.getStartedAt().toString() : null);

        return ResponseEntity.ok(response);
    }

    @PatchMapping("/{sessionId}/end")
    public ResponseEntity<Void> endSession(
            @PathVariable String sessionId,
            Authentication auth) {

        String userId = (String) auth.getPrincipal();

        java.util.Optional<Session> found = sessionRepository.findById(sessionId);

        if (found.isEmpty() || !found.get().getUserId().equals(userId)) {
            return ResponseEntity.notFound().build();
        }

        Session s = found.get();
        s.setStatus("ended");
        s.setEndedAt(LocalDateTime.now());
        sessionRepository.save(s);
        return ResponseEntity.ok().build();
    }
}