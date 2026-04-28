package com.seaquence.talkativ_backend.service;

import java.util.ArrayList;
import java.util.List;
import java.util.UUID;

import org.springframework.stereotype.Service;
import org.springframework.web.multipart.MultipartFile;

import com.seaquence.talkativ_backend.dto.InsightDto;
import com.seaquence.talkativ_backend.dto.RealtimeAnalysisResponse;
import com.seaquence.talkativ_backend.dto.TranscriptTurnDto;

import lombok.RequiredArgsConstructor;

@Service
@RequiredArgsConstructor
public class RealtimeAnalysisService {

    private final ClovaSpeechService clovaSpeechService;
    private final HonorificAnalysisService honorificAnalysisService;

    public RealtimeAnalysisResponse analyze(MultipartFile file, String sessionId) {
        if (file == null || file.isEmpty()) {
            throw new IllegalArgumentException("업로드된 오디오 파일이 없습니다.");
        }

        List<TranscriptTurnDto> turns = new ArrayList<>();
        List<InsightDto> insights = new ArrayList<>();

        clovaSpeechService.transcribeWithDiarization(file);
        String honorificResult = honorificAnalysisService.analyze("화자 1", "이거 오늘까지 해줘.", sessionId);

        String turnId = UUID.randomUUID().toString();

        turns.add(new TranscriptTurnDto(
                turnId,
                "화자 1",
                "이거 오늘까지 해줘.",
                "final"
        ));

        if ("risk".equals(honorificResult)) {
            insights.add(new InsightDto(
                    "insight-" + turnId,
                    "risk",
                    "반말 감지 — 존댓말이 필요한 상황입니다",
                    "이거 오늘까지 해주실 수 있으세요?",
                    turnId
            ));
        } else {
            insights.add(new InsightDto(
                    "insight-" + turnId,
                    "success",
                    "적절한 표현을 사용했어요",
                    null,
                    turnId
            ));
        }

        return new RealtimeAnalysisResponse(turns, insights);
    }
}