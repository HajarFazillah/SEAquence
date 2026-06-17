package com.seaquence.talkativ_backend.service;

import com.seaquence.talkativ_backend.dto.LoginRequest;
import com.seaquence.talkativ_backend.dto.LoginResponse;
import com.seaquence.talkativ_backend.dto.RegisterRequest;
import com.seaquence.talkativ_backend.dto.UserResponse;
import com.seaquence.talkativ_backend.dto.UserStats;
import com.seaquence.talkativ_backend.entity.Mistake;
import com.seaquence.talkativ_backend.entity.PasswordResetToken;
import com.seaquence.talkativ_backend.entity.Session;
import com.seaquence.talkativ_backend.entity.User;
import com.seaquence.talkativ_backend.repository.MistakeRepository;
import com.seaquence.talkativ_backend.repository.PasswordResetTokenRepository;
import com.seaquence.talkativ_backend.repository.SessionRepository;
import com.seaquence.talkativ_backend.repository.UserRepository;
import com.seaquence.talkativ_backend.security.JwtUtil;

import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Service;

import com.fasterxml.jackson.core.type.TypeReference;
import com.fasterxml.jackson.databind.ObjectMapper;

import java.security.SecureRandom;
import java.time.Duration;
import java.time.LocalDateTime;
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
    private final PasswordResetTokenRepository resetTokenRepository;
    private final EmailService emailService;

    private static final SecureRandom RANDOM = new SecureRandom();
    private static final ObjectMapper OBJECT_MAPPER = new ObjectMapper();

    public UserService(UserRepository userRepository, JwtUtil jwtUtil,
            PasswordEncoder passwordEncoder,
            SessionRepository sessionRepository,
            MistakeRepository mistakeRepository,
            PasswordResetTokenRepository resetTokenRepository,
            EmailService emailService) {
        this.userRepository = userRepository;
        this.jwtUtil = jwtUtil;
        this.passwordEncoder = passwordEncoder;
        this.sessionRepository = sessionRepository;
        this.mistakeRepository = mistakeRepository;
        this.resetTokenRepository = resetTokenRepository;
        this.emailService = emailService;
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
        user.setAge(request.getAge());
        user.setGender(request.getGender());
        user.setMemo(request.getMemo());
        user.setInterests(toJson(request.getInterests()));
        user.setDislikes(toJson(request.getDislikes()));
        user.setProvider("local");
        user.setPrivacyConsent(true);

        userRepository.save(user);
        return toResponse(user);
    }

    // Login user
    public LoginResponse login(LoginRequest request) {
        User user = userRepository.findByEmail(request.getEmail())
                .orElseThrow(() -> new RuntimeException("User not found"));

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
        if (request.getEmail() != null)
            user.setEmail(request.getEmail());
        if (request.getNativeLang() != null)
            user.setNativeLang(request.getNativeLang());
        if (request.getTargetLang() != null)
            user.setTargetLang(request.getTargetLang());
        if (request.getKoreanLevel() != null)
            user.setKoreanLevel(request.getKoreanLevel());
        if (request.getAge() != null)
            user.setAge(request.getAge());
        if (request.getGender() != null)
            user.setGender(request.getGender());
        if (request.getMemo() != null)
            user.setMemo(request.getMemo());
        if (request.getInterests() != null)
            user.setInterests(toJson(request.getInterests()));
        if (request.getDislikes() != null)
            user.setDislikes(toJson(request.getDislikes()));

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

    // Forgot password — generates OTP and sends it by email
    public void forgotPassword(String email) {
        // Silently succeed if email not found (prevents user enumeration)
        if (!userRepository.existsByEmail(email)) return;

        // Clear any previous tokens for this email
        resetTokenRepository.deleteAllByEmail(email);

        String code = String.format("%06d", RANDOM.nextInt(1_000_000));

        PasswordResetToken token = new PasswordResetToken();
        token.setEmail(email);
        token.setCode(code);
        token.setExpiresAt(LocalDateTime.now().plusMinutes(15));
        resetTokenRepository.save(token);

        emailService.sendPasswordResetCode(email, code);
    }

    // Reset password — validates OTP and sets new password
    public void resetPassword(String email, String code, String newPassword) {
        PasswordResetToken token = resetTokenRepository
                .findByEmailAndCodeAndUsedFalse(email, code)
                .orElseThrow(() -> new RuntimeException("Invalid or expired code."));

        if (LocalDateTime.now().isAfter(token.getExpiresAt())) {
            throw new RuntimeException("Code has expired. Please request a new one.");
        }

        User user = userRepository.findByEmail(email)
                .orElseThrow(() -> new RuntimeException("User not found."));

        user.setPassword(passwordEncoder.encode(newPassword));
        userRepository.save(user);

        token.setUsed(true);
        resetTokenRepository.save(token);
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
                user.getAvatarUrl(),
                user.getAge(),
                user.getGender(),
                user.getMemo(),
                fromJson(user.getInterests()),
                fromJson(user.getDislikes()));
    }

    private String toJson(List<String> values) {
        if (values == null) return null;
        try {
            return OBJECT_MAPPER.writeValueAsString(values);
        } catch (Exception e) {
            return "[]";
        }
    }

    private List<String> fromJson(String json) {
        if (json == null || json.isBlank()) return List.of();
        try {
            return OBJECT_MAPPER.readValue(json, new TypeReference<List<String>>() {});
        } catch (Exception e) {
            return List.of();
        }
    }
}
