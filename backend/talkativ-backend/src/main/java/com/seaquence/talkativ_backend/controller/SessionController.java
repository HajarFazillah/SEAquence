package com.seaquence.talkativ_backend.controller;

import com.seaquence.talkativ_backend.dto.SessionRequest;
import com.seaquence.talkativ_backend.dto.SessionResponse;
import com.seaquence.talkativ_backend.dto.SessionMessageRequest;
import com.seaquence.talkativ_backend.dto.SessionMessageResponse;
import com.seaquence.talkativ_backend.entity.ChatTurn;
import com.seaquence.talkativ_backend.entity.Session;
import com.seaquence.talkativ_backend.repository.ChatTurnRepository;
import com.seaquence.talkativ_backend.repository.SessionRepository;
import org.springframework.http.ResponseEntity;
import org.springframework.security.core.Authentication;
import org.springframework.transaction.annotation.Transactional;
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
    private final ChatTurnRepository chatTurnRepository;

    public SessionController(SessionRepository sessionRepository, ChatTurnRepository chatTurnRepository) {
        this.sessionRepository = sessionRepository;
        this.chatTurnRepository = chatTurnRepository;
    }

    @GetMapping
    public ResponseEntity<List<SessionResponse>> getSessions(
            @RequestParam(defaultValue = "active") String status,
            @RequestParam(required = false) String avatarId,
            Authentication auth) {

        String userId = (String) auth.getPrincipal();
        List<Session> sessions;

        // If avatarId is provided, filter by avatarId (ignore status)
        if (avatarId != null && !avatarId.isEmpty()) {
            sessions = sessionRepository.findByUserIdAndAvatarId(userId, avatarId);
        } else {
            sessions = sessionRepository.findByUserIdAndStatus(userId, status);
        }

        List<SessionResponse> response = sessions.stream()
                .map(s -> new SessionResponse(
                        s.getSessionId(), s.getAvatarId(), s.getAvatarName(),
                        s.getAvatarIcon(), s.getAvatarBg(), s.getSituation(),
                        s.getMood(), s.getDifficulty(), s.getSessionType(),
                        s.getStartedAt() != null ? s.getStartedAt().toString() : null,
                        s.getEndedAt() != null ? s.getEndedAt().toString() : null))
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
        session.setSessionType(request.getSessionType() != null ? request.getSessionType() : "chat");
        sessionRepository.save(session);

        SessionResponse response = new SessionResponse(
                session.getSessionId(), session.getAvatarId(), session.getAvatarName(),
                session.getAvatarIcon(), session.getAvatarBg(), session.getSituation(),
                session.getMood(), session.getDifficulty(), session.getSessionType(),
                session.getStartedAt() != null ? session.getStartedAt().toString() : null,
                session.getEndedAt() != null ? session.getEndedAt().toString() : null);

        return ResponseEntity.ok(response);
    }

    @DeleteMapping("/me")
    @Transactional
    public ResponseEntity<Void> deleteMySessionHistory(Authentication auth) {
        if (auth == null || auth.getPrincipal() == null) {
            return ResponseEntity.status(401).build();
        }
        String userId = (String) auth.getPrincipal();
        sessionRepository.deleteByUserId(userId);
        return ResponseEntity.noContent().build();
    }

    @GetMapping("/{sessionId}/messages")
    public ResponseEntity<List<SessionMessageResponse>> getMessages(
            @PathVariable String sessionId,
            Authentication auth) {
        Session session = ownedSession(sessionId, auth);
        if (session == null) return ResponseEntity.notFound().build();

        List<SessionMessageResponse> response = chatTurnRepository
                .findBySessionIdOrderByTurnNumberAsc(sessionId)
                .stream()
                .map(turn -> new SessionMessageResponse(
                        turn.getTurnNumber(),
                        turn.getRole(),
                        turn.getMessage(),
                        turn.getCreatedAt() != null ? turn.getCreatedAt().toString() : null))
                .toList();
        return ResponseEntity.ok(response);
    }

    @PutMapping("/{sessionId}/messages")
    @Transactional
    public ResponseEntity<Void> replaceMessages(
            @PathVariable String sessionId,
            @RequestBody List<SessionMessageRequest> messages,
            Authentication auth) {
        Session session = ownedSession(sessionId, auth);
        if (session == null) return ResponseEntity.notFound().build();

        chatTurnRepository.deleteBySessionId(sessionId);
        for (int i = 0; i < messages.size(); i++) {
            SessionMessageRequest request = messages.get(i);
            if (request.getContent() == null || request.getContent().isBlank()) continue;
            ChatTurn turn = new ChatTurn();
            turn.setSessionId(sessionId);
            turn.setTurnNumber(i + 1);
            turn.setRole("user".equals(request.getRole()) ? "user" : "assistant");
            turn.setMessage(request.getContent());
            chatTurnRepository.save(turn);
        }
        return ResponseEntity.noContent().build();
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
        s.setStatus("completed");
        s.setEndedAt(LocalDateTime.now());
        sessionRepository.save(s);

        return ResponseEntity.ok().build();
    }

    private Session ownedSession(String sessionId, Authentication auth) {
        if (auth == null || auth.getPrincipal() == null) return null;
        return sessionRepository.findById(sessionId)
                .filter(session -> session.getUserId().equals(auth.getPrincipal()))
                .orElse(null);
    }
}
