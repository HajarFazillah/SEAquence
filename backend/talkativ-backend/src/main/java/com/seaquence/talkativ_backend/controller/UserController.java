package com.seaquence.talkativ_backend.controller;

import com.seaquence.talkativ_backend.dto.ForgotPasswordRequest;
import com.seaquence.talkativ_backend.dto.RegisterRequest;
import com.seaquence.talkativ_backend.dto.ResetPasswordRequest;
import com.seaquence.talkativ_backend.dto.UserResponse;
import com.seaquence.talkativ_backend.service.UserService;
import com.seaquence.talkativ_backend.dto.LoginRequest;
import com.seaquence.talkativ_backend.dto.LoginResponse;
import com.seaquence.talkativ_backend.dto.UserStats;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import org.springframework.security.core.Authentication;

import java.util.List;

@RestController
@RequestMapping("/api/users")
@CrossOrigin(origins = "*")
public class UserController {

    private final UserService userService;

    public UserController(UserService userService) {
        this.userService = userService;
    }

    // GET all users
    @GetMapping
    public ResponseEntity<List<UserResponse>> getAllUsers() {
        return ResponseEntity.ok(userService.getAllUsers());
    }

    // GET user by ID
    @GetMapping("/{userId}")
    public ResponseEntity<UserResponse> getUserById(@PathVariable String userId) {
        return ResponseEntity.ok(userService.getUserById(userId));
    }

    // POST register new user
    @PostMapping("/register")
    public ResponseEntity<UserResponse> register(@RequestBody RegisterRequest request) {
        return ResponseEntity.ok(userService.register(request));
    }

    // PUT update user
    @PutMapping("/{userId}")
    public ResponseEntity<UserResponse> updateUser(@PathVariable String userId,
            @RequestBody RegisterRequest request) {
        return ResponseEntity.ok(userService.updateUser(userId, request));
    }

    // DELETE user
    @DeleteMapping("/{userId}")
    public ResponseEntity<String> deleteUser(@PathVariable String userId) {
        userService.deleteUser(userId);
        return ResponseEntity.ok("User deleted successfully");
    }

    @PostMapping("/login")
    public ResponseEntity<LoginResponse> login(@RequestBody LoginRequest request) {
        return ResponseEntity.ok(userService.login(request));
    }

    @GetMapping("/me")
    public ResponseEntity<UserResponse> getMe(Authentication auth) {
        String userId = (String) auth.getPrincipal();
        return ResponseEntity.ok(userService.getMe(userId));
    }

    @PutMapping("/me")
    public ResponseEntity<UserResponse> updateMe(
            @RequestBody RegisterRequest request,
            Authentication auth) {
        String userId = (String) auth.getPrincipal();
        return ResponseEntity.ok(userService.updateUser(userId, request));
    }

    @GetMapping("/me/stats")
    public ResponseEntity<UserStats> getMyStats(Authentication auth) {
        String userId = (String) auth.getPrincipal();
        return ResponseEntity.ok(userService.getMyStats(userId));
    }

    @PostMapping("/forgot-password")
    public ResponseEntity<String> forgotPassword(@RequestBody ForgotPasswordRequest request) {
        try {
            userService.forgotPassword(request.getEmail());
        } catch (Exception ignored) {
            // Swallow all errors — never reveal whether the email exists
        }
        return ResponseEntity.ok("If that email is registered, a reset code has been sent.");
    }

    @PostMapping("/reset-password")
    public ResponseEntity<?> resetPassword(@RequestBody ResetPasswordRequest request) {
        try {
            userService.resetPassword(request.getEmail(), request.getCode(), request.getNewPassword());
            return ResponseEntity.ok("Password reset successfully.");
        } catch (RuntimeException e) {
            return ResponseEntity.badRequest().body(java.util.Map.of("message", e.getMessage()));
        }
    }

}
