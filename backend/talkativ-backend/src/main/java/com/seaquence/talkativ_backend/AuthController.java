package com.seaquence.talkativ_backend;

import java.util.Map;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/auth")
public class AuthController {

    @PostMapping("/kakao")
    public Map<String, String> kakaoLogin() {
        return Map.of(
            "accessToken", "stub-token-12345",
            "userId", "stub-user-001"
        );
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
