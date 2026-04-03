package com.seaquence.talkativ_backend.service;

import java.util.List;
import java.util.stream.Collectors;

import org.springframework.stereotype.Service;

import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.seaquence.talkativ_backend.dto.AvatarRequest;
import com.seaquence.talkativ_backend.dto.AvatarResponse;
import com.seaquence.talkativ_backend.entity.Avatar;
import com.seaquence.talkativ_backend.repository.AvatarRepository;
import com.seaquence.talkativ_backend.repository.UserRepository;

@Service
public class AvatarService {

    private final AvatarRepository avatarRepository;
    private final UserRepository userRepository;
    private final ObjectMapper objectMapper;

    public AvatarService(AvatarRepository avatarRepository,
            UserRepository userRepository,
            ObjectMapper objectMapper) {
        this.avatarRepository = avatarRepository;
        this.userRepository = userRepository;
        this.objectMapper = objectMapper;
    }

    public List<AvatarResponse> getAvatarsByUser(String userId) {
        if (!userRepository.existsById(userId)) {
            throw new RuntimeException("User not found");
        }
        return avatarRepository.findByUserId(userId)
                .stream()
                .map(AvatarResponse::from)
                .collect(Collectors.toList());
    }

    public AvatarResponse createAvatar(String userId, AvatarRequest request) {
        if (!userRepository.existsById(userId)) {
            throw new RuntimeException("User not found");
        }
        Avatar avatar = new Avatar();
        avatar.setUserId(userId);
        avatar.setIsActive(true);
        applyRequest(avatar, request);
        return AvatarResponse.from(avatarRepository.save(avatar));
    }

    public AvatarResponse updateAvatar(String userId, Long avatarId, AvatarRequest request) {
        Avatar avatar = avatarRepository.findById(avatarId)
                .orElseThrow(() -> new RuntimeException("Avatar not found"));

        if (!avatar.getUserId().equals(userId)) {
            throw new RuntimeException("Unauthorized");
        }

        applyRequest(avatar, request);
        return AvatarResponse.from(avatarRepository.save(avatar));
    }

    public void deleteAvatar(String userId, Long avatarId) {
        Avatar avatar = avatarRepository.findById(avatarId)
                .orElseThrow(() -> new RuntimeException("Avatar not found"));

        if (!avatar.getUserId().equals(userId)) {
            throw new RuntimeException("Unauthorized");
        }

        avatarRepository.delete(avatar);
    }

    // ── Private helpers ───────────────────────────────────────────────────────
    private void applyRequest(Avatar avatar, AvatarRequest request) {
        // Fix name_ko NULL constraint
        String nameKo = request.getNameKo();
        if (nameKo == null || nameKo.trim().isEmpty()) {
            nameKo = "이름없음";
        }
        avatar.setNameKo(nameKo.trim());

        avatar.setNameEn(request.getNameEn());
        avatar.setAge(request.getAge());
        avatar.setGender(request.getGender());
        avatar.setAvatarType(request.getAvatarType());
        avatar.setAvatarBg(request.getAvatarBg());
        avatar.setIcon(request.getIcon());
        avatar.setRole(request.getRole());
        avatar.setCustomRole(request.getCustomRole() != null ? request.getCustomRole().trim() : "");
        avatar.setRelationshipDescription(request.getRelationshipDescription());
        avatar.setDifficulty(request.getDifficulty());
        avatar.setDescription(request.getDescription());
        avatar.setSpeakingStyle(request.getSpeakingStyle());
        avatar.setMemo(request.getMemo());
        avatar.setFormalityToUser(request.getFormalityToUser());
        avatar.setFormalityFromUser(request.getFormalityFromUser());
        avatar.setBio(request.getBio());
        avatar.setPersonalityTraits(toJson(request.getPersonalityTraits()));
        avatar.setInterests(toJson(request.getInterests()));
        avatar.setDislikes(toJson(request.getDislikes()));
    }

    private String toJson(List<String> list) {
        if (list == null)
            return "[]";
        try {
            return objectMapper.writeValueAsString(list);
        } catch (JsonProcessingException e) {
            return "[]";
        }
    }
}