package com.seaquence.talkativ_backend.controller;
import com.seaquence.talkativ_backend.entity.User;
import com.seaquence.talkativ_backend.repository.UserRepository;
import com.seaquence.talkativ_backend.security.JwtUtil;
import org.springframework.web.bind.annotation.*;
import java.util.Map;
import java.util.Optional;
import java.util.UUID;
@RestController
@RequestMapping("/auth")
public class AuthController {
    private final UserRepository userRepository;
    private final JwtUtil jwtUtil;
    public AuthController(UserRepository userRepository, JwtUtil jwtUtil) {
        this.userRepository = userRepository;
        this.jwtUtil = jwtUtil;
    }
    @PostMapping("/kakao")
    public Map<String, String> kakaoLogin(@RequestBody Map<String, String> body) {
        String kakaoId = body.get("kakaoId");
        String email = body.getOrDefault("email", kakaoId + "@kakao.com");
        String nickname = body.getOrDefault("nickname", "Kakao User");
        String profileImageUrl = body.getOrDefault("profileImageUrl", null);
        Optional<User> existing = userRepository.findByEmail(email);
        User user;
        if (existing.isPresent()) {
            user = existing.get();
            user.setUsername(nickname);
            if (profileImageUrl != null) user.setAvatarUrl(profileImageUrl);
            userRepository.save(user);
        } else {
            user = new User();
            user.setUserId(UUID.randomUUID().toString());
            user.setUsername(nickname);
            user.setEmail(email);
            user.setPassword(null);
            user.setProvider("kakao");
            user.setNativeLang("en");
            user.setTargetLang("ko");
            user.setKoreanLevel("intermediate");
            user.setPrivacyConsent(true);
            user.setAvatarUrl(profileImageUrl);
            userRepository.save(user);
        }
        String token = jwtUtil.generateToken(user.getUserId(), user.getEmail());
        return Map.of("token", token, "userId", user.getUserId());
    }
    @PostMapping("/google")
    public Map<String, String> googleLogin(@RequestBody Map<String, String> body) {
        String googleId = body.get("googleId");
        String email = body.getOrDefault("email", googleId + "@google.com");
        String nickname = body.getOrDefault("nickname", "Google User");
        String profileImageUrl = body.getOrDefault("profileImageUrl", null);
        Optional<User> existing = userRepository.findByEmail(email);
        User user;
        if (existing.isPresent()) {
            user = existing.get();
            user.setUsername(nickname);
            if (profileImageUrl != null) user.setAvatarUrl(profileImageUrl);
            userRepository.save(user);
        } else {
            user = new User();
            user.setUserId(UUID.randomUUID().toString());
            user.setUsername(nickname);
            user.setEmail(email);
            user.setPassword(null);
            user.setProvider("google");
            user.setNativeLang("en");
            user.setTargetLang("ko");
            user.setKoreanLevel("intermediate");
            user.setPrivacyConsent(true);
            user.setAvatarUrl(profileImageUrl);
            userRepository.save(user);
        }
        String token = jwtUtil.generateToken(user.getUserId(), user.getEmail());
        return Map.of("token", token, "userId", user.getUserId());
    }
    @GetMapping("/me")
    public Map<String, String> getMe() {
        return Map.of(
            "userId", "stub-user-001",
            "name", "Talkativ User",
            "email", "user@talkativ.com"
        );
    }
}