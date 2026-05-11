package com.seaquence.talkativ_backend.controller;

import com.seaquence.talkativ_backend.dto.RealtimeAnalysisResponse;
import com.seaquence.talkativ_backend.service.RealtimeAnalysisService;
import lombok.RequiredArgsConstructor;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestPart;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.multipart.MultipartFile;

@RestController
@RequestMapping("/realtime")
@RequiredArgsConstructor
public class RealtimeAnalysisController {

    private final RealtimeAnalysisService realtimeAnalysisService;

    @PostMapping(value = "/analyze", consumes = MediaType.MULTIPART_FORM_DATA_VALUE)
    public ResponseEntity<RealtimeAnalysisResponse> analyzeRealtime(
            @RequestPart("file") MultipartFile file,
            @RequestPart(value = "avatarRole", required = false) String avatarRole,
            @RequestPart(value = "userId", required = false) String userId,
            @RequestPart(value = "sessionId", required = false) String sessionId,
            @RequestPart(value = "expectedSpeechLevel", required = false) String expectedSpeechLevel,
            @RequestPart(value = "userSpeakerLabel", required = false) String userSpeakerLabel,
            @RequestPart(value = "chunkIndex", required = false) String chunkIndex
    ) {
        RealtimeAnalysisResponse response = realtimeAnalysisService.analyzeRealtimeAudio(
                file, avatarRole, userId, sessionId, expectedSpeechLevel, userSpeakerLabel, chunkIndex
        );
        return ResponseEntity.ok(response);
    }
}
