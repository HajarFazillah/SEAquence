package com.seaquence.talkativ_backend.dto;

public class UserStats {
    private int completedSessions;
    private int learnedExpressions;
    private int practiceMinutes;
    private int progressPercent;
    private String topMistakeType;

    public UserStats(int completedSessions, int learnedExpressions,
                     int practiceMinutes, int progressPercent, String topMistakeType) {
        this.completedSessions = completedSessions;
        this.learnedExpressions = learnedExpressions;
        this.practiceMinutes = practiceMinutes;
        this.progressPercent = progressPercent;
        this.topMistakeType = topMistakeType;
    }

    public int getCompletedSessions() { return completedSessions; }
    public int getLearnedExpressions() { return learnedExpressions; }
    public int getPracticeMinutes() { return practiceMinutes; }
    public int getProgressPercent() { return progressPercent; }
    public String getTopMistakeType() { return topMistakeType; }
}