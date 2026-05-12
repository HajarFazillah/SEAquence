package com.seaquence.talkativ_backend.service;

import java.util.List;
import java.util.Locale;
import java.util.Set;
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
    private static final Set<String> EASY_ROLES = Set.of(
            "friend", "close_friend", "classmate", "classmate_formal",
            "roommate", "club_member", "younger_sibling", "cousin");
    private static final Set<String> HARD_ROLES = Set.of(
            "parent", "grandparent", "professor", "teacher",
            "team_leader", "boss", "ceo", "client", "doctor");
    private static final List<String> HARD_ROLE_KEYWORDS = List.of(
            "교수", "선생", "부장", "상사", "팀장", "대표", "사장",
            "고객", "클라이언트", "의사", "면접관", "임원", "원장",
            "회장", "부모", "아버지", "어머니", "할머니", "할아버지");
    private static final List<String> EASY_ROLE_KEYWORDS = List.of(
            "친구", "절친", "동기", "룸메", "룸메이트", "동아리", "동생", "사촌");
    private static final List<String> MEDIUM_ROLE_KEYWORDS = List.of(
            "선배", "후배", "동료", "팀원", "튜터", "이웃", "직원",
            "점원", "기사", "배달", "처음 만난", "낯선");


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
        avatar.setDifficulty(deriveDifficulty(
                request.getRole(),
                request.getCustomRole(),
                request.getFormalityFromUser()));
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

    private String deriveDifficulty(String role, String customRole, String formalityFromUser) {
        String normalizedRole = role == null ? "" : role.trim().toLowerCase(Locale.ROOT);
        String normalizedCustomRole = customRole == null ? "" : customRole.trim();
        String normalizedFormality = formalityFromUser == null ? "" : formalityFromUser.trim().toLowerCase(Locale.ROOT);

        if (HARD_ROLES.contains(normalizedRole)) {
            return "hard";
        }
        if (EASY_ROLES.contains(normalizedRole)) {
            return "easy";
        }

        if (!normalizedCustomRole.isEmpty()) {
            if (containsAnyKeyword(normalizedCustomRole, HARD_ROLE_KEYWORDS)) {
                return "hard";
            }
            if (containsAnyKeyword(normalizedCustomRole, EASY_ROLE_KEYWORDS)) {
                return "easy";
            }
            if (containsAnyKeyword(normalizedCustomRole, MEDIUM_ROLE_KEYWORDS)) {
                return "medium";
            }
        }

        if ("formal".equals(normalizedFormality)) {
            return "hard";
        }
        if ("informal".equals(normalizedFormality)) {
            return "easy";
        }
        return "medium";
    }

    private boolean containsAnyKeyword(String value, List<String> keywords) {
        for (String keyword : keywords) {
            if (value.contains(keyword)) {
                return true;
            }
        }
        return false;
    }
}
