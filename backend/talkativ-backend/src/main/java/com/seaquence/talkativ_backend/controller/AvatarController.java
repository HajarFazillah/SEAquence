package com.seaquence.talkativ_backend.controller;

import com.seaquence.talkativ_backend.dto.AvatarRequest;
import com.seaquence.talkativ_backend.dto.AvatarResponse;
import com.seaquence.talkativ_backend.service.AvatarService;
import com.seaquence.talkativ_backend.security.JwtUtil;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import java.util.List;

@RestController
@RequestMapping("/api/avatars")
@CrossOrigin(origins = "*")
public class AvatarController {

    private final AvatarService avatarService;
    private final JwtUtil jwtUtil;

    public AvatarController(AvatarService avatarService, JwtUtil jwtUtil) {
        this.avatarService = avatarService;
        this.jwtUtil = jwtUtil;
    }

    private String extractUserId(String authHeader) {
        String token = authHeader.replace("Bearer ", "");
        return jwtUtil.extractUserId(token);
    }

    @GetMapping
    public ResponseEntity<List<AvatarResponse>> getAvatars(
            @RequestHeader("Authorization") String authHeader) {
        String userId = extractUserId(authHeader);
        return ResponseEntity.ok(avatarService.getAvatarsByUser(userId));
    }

    @PostMapping
    public ResponseEntity<AvatarResponse> createAvatar(
            @RequestHeader("Authorization") String authHeader,
            @RequestBody AvatarRequest request) {
        String userId = extractUserId(authHeader);
        return ResponseEntity.ok(avatarService.createAvatar(userId, request));
    }

    @PutMapping("/{avatarId}")
    public ResponseEntity<AvatarResponse> updateAvatar(
            @RequestHeader("Authorization") String authHeader,
            @PathVariable Long avatarId,
            @RequestBody AvatarRequest request) {
        String userId = extractUserId(authHeader);
        return ResponseEntity.ok(avatarService.updateAvatar(userId, avatarId, request));
    }

    @DeleteMapping("/{avatarId}")
    public ResponseEntity<String> deleteAvatar(
            @RequestHeader("Authorization") String authHeader,
            @PathVariable Long avatarId) {
        String userId = extractUserId(authHeader);
        avatarService.deleteAvatar(userId, avatarId);
        return ResponseEntity.ok("Avatar deleted successfully");
    }
}