package com.seaquence.talkativ_backend.entity;

import jakarta.persistence.*;
import org.hibernate.annotations.CreationTimestamp;
import java.time.LocalDateTime;

@Entity
@Table(name = "mistakes")
public class Mistake {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(name = "session_id", nullable = false, length = 255)
    private String sessionId;

    @Column(name = "user_id", nullable = false, length = 36)
    private String userId;

    @Column(name = "turn_number")
    private Integer turnNumber;

    @Column(name = "original_text", nullable = false, columnDefinition = "TEXT")
    private String originalText;

    @Column(name = "corrected_text", nullable = false, columnDefinition = "TEXT")
    private String correctedText;

    @Column(name = "correction_type", length = 50)
    private String correctionType;

    @Column(name = "severity", length = 20)
    private String severity;

    @Column(name = "explanation", columnDefinition = "TEXT")
    private String explanation;

    @Column(name = "tip", columnDefinition = "TEXT")
    private String tip;

    @CreationTimestamp
    @Column(name = "created_at", updatable = false)
    private LocalDateTime createdAt;

    // Getters and Setters
    public Long getId() { return id; }
    public void setId(Long id) { this.id = id; }

    public String getSessionId() { return sessionId; }
    public void setSessionId(String sessionId) { this.sessionId = sessionId; }

    public String getUserId() { return userId; }
    public void setUserId(String userId) { this.userId = userId; }

    public Integer getTurnNumber() { return turnNumber; }
    public void setTurnNumber(Integer turnNumber) { this.turnNumber = turnNumber; }

    public String getOriginalText() { return originalText; }
    public void setOriginalText(String originalText) { this.originalText = originalText; }

    public String getCorrectedText() { return correctedText; }
    public void setCorrectedText(String correctedText) { this.correctedText = correctedText; }

    public String getCorrectionType() { return correctionType; }
    public void setCorrectionType(String correctionType) { this.correctionType = correctionType; }

    public String getSeverity() { return severity; }
    public void setSeverity(String severity) { this.severity = severity; }

    public String getExplanation() { return explanation; }
    public void setExplanation(String explanation) { this.explanation = explanation; }

    public String getTip() { return tip; }
    public void setTip(String tip) { this.tip = tip; }

    public LocalDateTime getCreatedAt() { return createdAt; }
}
