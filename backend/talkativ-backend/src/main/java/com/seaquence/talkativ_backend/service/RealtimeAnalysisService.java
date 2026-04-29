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
                String turnId = "turn-" + idx;

                turns.add(new TranscriptTurnDto(
                        turnId,
                        turn.getSpeaker(),
                        turn.getText(),
                        "final"
                ));

                idx++;
            }
        }

        if (!turns.isEmpty()) {
            insights.add(new InsightDto(
                    "insight-1",
                    "success",
                    "Realtime transcription completed.",
                    "Proceed to show the diarized turns in the UI.",
                    turns.get(0).getId()
            ));
        }

        return new RealtimeAnalysisResponse(turns, insights);
    }
}