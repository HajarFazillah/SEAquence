package com.seaquence.talkativ_backend.dto;

public class UserStats {
    private int completedSessions;
    private int learnedExpressions;
    private int practiceMinutes;
    private int progressPercent;

    public UserStats(int completedSessions, int learnedExpressions,
                     int practiceMinutes, int progressPercent) {
        this.completedSessions = completedSessions;
        this.learnedExpressions = learnedExpressions;
        this.practiceMinutes = practiceMinutes;
        this.progressPercent = progressPercent;
    }

    // Getters
    public int getCompletedSessions() { return completedSessions; }
    public int getLearnedExpressions() { return learnedExpressions; }
    public int getPracticeMinutes() { return practiceMinutes; }
    public int getProgressPercent() { return progressPercent; }
}