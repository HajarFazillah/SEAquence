package com.seaquence.talkativ_backend.service;

import com.seaquence.talkativ_backend.dto.AvatarRequest;
import com.seaquence.talkativ_backend.dto.AvatarResponse;
import com.seaquence.talkativ_backend.entity.Avatar;
import com.seaquence.talkativ_backend.repository.AvatarRepository;
import com.seaquence.talkativ_backend.repository.UserRepository;
import org.springframework.stereotype.Service;

import java.util.List;
import java.util.stream.Collectors;

@Service
public class AvatarService {

    private final AvatarRepository avatarRepository;
    private final UserRepository userRepository;

    public AvatarService(AvatarRepository avatarRepository, UserRepository userRepository) {
        this.avatarRepository = avatarRepository;
        this.userRepository = userRepository;
    }

    // Create avatar for a user
    public AvatarResponse createAvatar(String userId, AvatarRequest request) {
        if (!userRepository.existsById(userId)) {
            throw new RuntimeException("User not found");
        }

        Avatar avatar = new Avatar();
        avatar.setUserId(userId);
        avatar.setImageUrl(request.getImageUrl());
        avatar.setStyle(request.getStyle());
        avatar.setIsActive(true);

        avatarRepository.save(avatar);
        return toResponse(avatar);
    }

    // Get all avatars for a user
    public List<AvatarResponse> getAvatarsByUser(String userId) {
        return avatarRepository.findByUserId(userId)
                .stream()
                .map(this::toResponse)
                .collect(Collectors.toList());
    }

    // Update avatar
    public AvatarResponse updateAvatar(Long avatarId, AvatarRequest request) {
        Avatar avatar = avatarRepository.findById(avatarId)
                .orElseThrow(() -> new RuntimeException("Avatar not found"));

        if (request.getImageUrl() != null) avatar.setImageUrl(request.getImageUrl());
        if (request.getStyle() != null) avatar.setStyle(request.getStyle());

        avatarRepository.save(avatar);
        return toResponse(avatar);
    }

    // Delete avatar
    public void deleteAvatar(Long avatarId) {
        if (!avatarRepository.existsById(avatarId)) {
            throw new RuntimeException("Avatar not found");
        }
        avatarRepository.deleteById(avatarId);
    }

    // Convert entity to response DTO
    private AvatarResponse toResponse(Avatar avatar) {
        return new AvatarResponse(
                avatar.getAvatarId(),
                avatar.getUserId(),
                avatar.getImageUrl(),
                avatar.getStyle(),
                avatar.getIsActive()
        );
    }
}
