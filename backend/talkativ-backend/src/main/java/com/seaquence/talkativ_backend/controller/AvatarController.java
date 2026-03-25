package com.seaquence.talkativ_backend.controller;

import com.seaquence.talkativ_backend.dto.AvatarRequest;
import com.seaquence.talkativ_backend.dto.AvatarResponse;
import com.seaquence.talkativ_backend.service.AvatarService;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@RestController
@RequestMapping("/api")
@CrossOrigin(origins = "*")
public class AvatarController {

    private final AvatarService avatarService;

    public AvatarController(AvatarService avatarService) {
        this.avatarService = avatarService;
    }

    // GET all avatars for a user
    @GetMapping("/users/{userId}/avatars")
    public ResponseEntity<List<AvatarResponse>> getAvatars(@PathVariable String userId) {
        return ResponseEntity.ok(avatarService.getAvatarsByUser(userId));
    }

    // POST create avatar for a user
    @PostMapping("/users/{userId}/avatars")
    public ResponseEntity<AvatarResponse> createAvatar(@PathVariable String userId,
                                                        @RequestBody AvatarRequest request) {
        return ResponseEntity.ok(avatarService.createAvatar(userId, request));
    }

    // PUT update avatar
    @PutMapping("/avatars/{avatarId}")
    public ResponseEntity<AvatarResponse> updateAvatar(@PathVariable Long avatarId,
                                                        @RequestBody AvatarRequest request) {
        return ResponseEntity.ok(avatarService.updateAvatar(avatarId, request));
    }

    // DELETE avatar
    @DeleteMapping("/avatars/{avatarId}")
    public ResponseEntity<String> deleteAvatar(@PathVariable Long avatarId) {
        avatarService.deleteAvatar(avatarId);
        return ResponseEntity.ok("Avatar deleted successfully");
    }
}
