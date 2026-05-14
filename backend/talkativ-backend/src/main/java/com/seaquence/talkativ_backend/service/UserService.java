package com.seaquence.talkativ_backend.service;

import com.seaquence.talkativ_backend.dto.LoginRequest;
import com.seaquence.talkativ_backend.dto.LoginResponse;
import com.seaquence.talkativ_backend.dto.RegisterRequest;
import com.seaquence.talkativ_backend.dto.UserResponse;
import com.seaquence.talkativ_backend.dto.UserStats;
import com.seaquence.talkativ_backend.entity.Mistake;
import com.seaquence.talkativ_backend.entity.Session;
import com.seaquence.talkativ_backend.entity.User;
import com.seaquence.talkativ_backend.repository.MistakeRepository;
import com.seaquence.talkativ_backend.repository.SessionRepository;
import com.seaquence.talkativ_backend.repository.UserRepository;
import com.seaquence.talkativ_backend.security.JwtUtil;

import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Service;

import java.time.Duration;
import java.util.Comparator;
import java.util.List;
import java.util.Map;
import java.util.UUID;
import java.util.stream.Collectors;

@Service
public class UserService {

    private final UserRepository userRepository;
    private final JwtUtil jwtUtil;
    private final PasswordEncoder passwordEncoder;
    private final SessionRepository sessionRepository;
    private final MistakeRepository mistakeRepository;

    public UserService(UserRepository userRepository, JwtUtil jwtUtil,
            PasswordEncoder passwordEncoder,
            SessionRepository sessionRepository,
            MistakeRepository mistakeRepository) {
        this.userRepository = userRepository;
        this.jwtUtil = jwtUtil;
        this.passwordEncoder = passwordEncoder;
        this.sessionRepository = sessionRepository;
        this.mistakeRepository = mistakeRepository;
    }

    // Register new user
    public UserResponse register(RegisterRequest request) {
        if (userRepository.existsByEmail(request.getEmail())) {
            throw new RuntimeException("Email already in use");
        }
        if (userRepository.existsByUsername(request.getUsername())) {
            throw new RuntimeException("Username already taken");
        }

        User user = new User();
        user.setUserId(UUID.randomUUID().toString());
        user.setUsername(request.getUsername());
        user.setEmail(request.getEmail());
        user.setPassword(passwordEncoder.encode(request.getPassword())); // ← already correct
        user.setNativeLang(request.getNativeLang());
        user.setTargetLang(request.getTargetLang());
        user.setKoreanLevel(request.getKoreanLevel() != null ? request.getKoreanLevel() : "intermediate");
        user.setProvider("local");
        user.setPrivacyConsent(true);

        userRepository.save(user);
        return toResponse(user);
    }

    // Login user
    public LoginResponse login(LoginRequest request) {
        User user = userRepository.findByEmail(request.getEmail())
                .orElseThrow(() -> new RuntimeException("User not found"));

        // ← FIXED: was .equals() which doesn't work with BCrypt
        if (!passwordEncoder.matches(request.getPassword(), user.getPassword())) {
            throw new RuntimeException("Invalid password");
        }

        String token = jwtUtil.generateToken(user.getUserId(), user.getEmail());
        return new LoginResponse(token, toResponse(user));
    }

    // Get user by ID
    public UserResponse getUserById(String userId) {
        User user = userRepository.findById(userId)
                .orElseThrow(() -> new RuntimeException("User not found"));
        return toResponse(user);
    }

    // Get all users
    public List<UserResponse> getAllUsers() {
        return userRepository.findAll()
                .stream()
                .map(this::toResponse)
                .collect(Collectors.toList());
    }

    // Update user
    public UserResponse updateUser(String userId, RegisterRequest request) {
        User user = userRepository.findById(userId)
                .orElseThrow(() -> new RuntimeException("User not found"));

        if (request.getUsername() != null)
            user.setUsername(request.getUsername());
        if (request.getNativeLang() != null)
            user.setNativeLang(request.getNativeLang());
        if (request.getTargetLang() != null)
            user.setTargetLang(request.getTargetLang());
        if (request.getKoreanLevel() != null)
            user.setKoreanLevel(request.getKoreanLevel());

        userRepository.save(user);
        return toResponse(user);
    }

    // Delete user
    public void deleteUser(String userId) {
        if (!userRepository.existsById(userId)) {
            throw new RuntimeException("User not found");
        }
        userRepository.deleteById(userId);
    }

    // Get current logged-in user
    public UserResponse getMe(String userId) {
        User user = userRepository.findById(userId)
                .orElseThrow(() -> new RuntimeException("User not found"));
        return toResponse(user);
    }

    // Get current user's stats
    public UserStats getMyStats(String userId) {
        // completedSessions: sessions with status "completed"
        List<Session> completed = sessionRepository.findByUserIdAndStatus(userId, "completed");
        int completedSessions = completed.size();

        // practiceMinutes: sum of (endedAt - startedAt) for sessions that have both timestamps
        int practiceMinutes = completed.stream()
            .filter(s -> s.getStartedAt() != null && s.getEndedAt() != null)
            .mapToInt(s -> (int) Duration.between(s.getStartedAt(), s.getEndedAt()).toMinutes())
            .sum();

        // topMistakeType: most frequent correction_type across all user mistakes
        List<Mistake> mistakes = mistakeRepository.findByUserId(userId);
        String topMistakeType = mistakes.stream()
            .filter(m -> m.getCorrectionType() != null && !m.getCorrectionType().isBlank())
            .collect(Collectors.groupingBy(Mistake::getCorrectionType, Collectors.counting()))
            .entrySet().stream()
            .max(Map.Entry.comparingByValue())
            .map(Map.Entry::getKey)
            .orElse(null);

        return new UserStats(completedSessions, mistakes.size(), practiceMinutes, 0, topMistakeType);
    }

    // Convert entity to response DTO
    private UserResponse toResponse(User user) {
    return new UserResponse(
            user.getUserId(),
            user.getUsername(),
            user.getEmail(),
            user.getNativeLang(),
            user.getTargetLang(),
            user.getKoreanLevel(),
            user.getProvider(),
            user.getAvatarUrl());
}
}