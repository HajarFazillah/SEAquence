package com.seaquence.talkativ_backend.service;

import com.seaquence.talkativ_backend.dto.InsightDto;
import com.seaquence.talkativ_backend.dto.RealtimeAnalysisResponse;
import com.seaquence.talkativ_backend.dto.TranscriptTurnDto;
import org.springframework.stereotype.Service;
import org.springframework.web.multipart.MultipartFile;

import java.util.ArrayList;
import java.util.List;

@Service
public class RealtimeAnalysisService {

    private final ClovaSpeechService clovaSpeechService;

    public RealtimeAnalysisService(ClovaSpeechService clovaSpeechService) {
        this.clovaSpeechService = clovaSpeechService;
    }

    public RealtimeAnalysisResponse analyzeRealtimeAudio(MultipartFile file) {
        ClovaSpeechService.ClovaSpeechResult speechResult = clovaSpeechService.transcribeWithDiarization(file);

        List<TranscriptTurnDto> turns = new ArrayList<>();
        List<InsightDto> insights = new ArrayList<>();

        if (speechResult.getTurns() != null) {
            int idx = 1;
            for (ClovaSpeechService.SpeakerTurn turn : speechResult.getTurns()) {
                if (turn.getText() == null || turn.getText().isBlank()) {
                    continue;
                }
                String turnId = "turn-" + idx;

                turns.add(new TranscriptTurnDto(
                        turnId,
                        (turn.getSpeaker() == null || turn.getSpeaker().isBlank()) ? "나" : turn.getSpeaker(),
                        turn.getText(),
                        "final"
                ));

                idx++;
            }
        }

        if (turns.isEmpty() && speechResult.getFullText() != null && !speechResult.getFullText().isBlank()) {
            turns.add(new TranscriptTurnDto(
                    "turn-1",
                    "나",
                    speechResult.getFullText().trim(),
                    "final"
            ));
        }

        if (!turns.isEmpty()) {
            insights.add(new InsightDto(
                    "insight-1",
                    "success",
                    "음성이 텍스트로 잘 인식됐어요.",
                    "인식된 문장을 화면에서 바로 확인해 보세요.",
                    turns.get(0).getId()
            ));
        } else {
            insights.add(new InsightDto(
                    "insight-empty",
                    "risk",
                    "음성은 업로드됐지만 텍스트로 인식되지 않았어요.",
                    "조금 더 길고 또렷하게 말한 뒤 다시 시도해 보세요.",
                    ""
            ));
        }

        return new RealtimeAnalysisResponse(turns, insights);
    }
}
