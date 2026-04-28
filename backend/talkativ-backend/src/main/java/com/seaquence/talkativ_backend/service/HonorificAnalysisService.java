package com.seaquence.talkativ_backend.service;

import org.springframework.stereotype.Service;

@Service
public class HonorificAnalysisService {

    public String analyze(String speaker, String text, String sessionId) {
        if (text.contains("해줘")) {
            return "risk";
        }
        return "success";
    }
}