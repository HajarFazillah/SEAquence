package com.seaquence.talkativ_backend.service;

import com.seaquence.talkativ_backend.dto.LoginRequest;
import com.seaquence.talkativ_backend.dto.LoginResponse;
import com.seaquence.talkativ_backend.dto.RegisterRequest;
import com.seaquence.talkativ_backend.dto.UserResponse;
import com.seaquence.talkativ_backend.dto.UserStats;
import com.seaquence.talkativ_backend.entity.User;
import com.seaquence.talkativ_backend.repository.UserRepository;
import com.seaquence.talkativ_backend.security.JwtUtil;

import org.springframework.security.crypto.password.PasswordEncoder; // ← ADDED
import org.springframework.stereotype.Service;

import java.util.List;
import java.util.UUID;
import java.util.stream.Collectors;

@Service
public class UserService {

    private final UserRepository userRepository;
    private final JwtUtil jwtUtil;
    private final PasswordEncoder passwordEncoder; // ← ADDED

    public UserService(UserRepository userRepository, JwtUtil jwtUtil,
            PasswordEncoder passwordEncoder) { // ← ADDED
        this.userRepository = userRepository;
        this.jwtUtil = jwtUtil;
        this.passwordEncoder = passwordEncoder; // ← ADDED
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
        // Placeholder until SessionRepository is ready
        return new UserStats(0, 0, 0, 0);
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
                user.getProvider());
    }
}