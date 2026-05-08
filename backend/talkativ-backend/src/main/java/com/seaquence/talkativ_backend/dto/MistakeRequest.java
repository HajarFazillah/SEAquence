package com.seaquence.talkativ_backend.dto;

import java.util.List;

public class MistakeRequest {

    private String sessionId;
    private Integer turnNumber;
    private List<MistakeItem> mistakes;

    public String getSessionId() { return sessionId; }
    public void setSessionId(String sessionId) { this.sessionId = sessionId; }

    public Integer getTurnNumber() { return turnNumber; }
    public void setTurnNumber(Integer turnNumber) { this.turnNumber = turnNumber; }

    public List<MistakeItem> getMistakes() { return mistakes; }
    public void setMistakes(List<MistakeItem> mistakes) { this.mistakes = mistakes; }

    public static class MistakeItem {
        private String originalText;
        private String correctedText;
        private String correctionType;
        private String severity;
        private String explanation;
        private String tip;

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
    }
}
