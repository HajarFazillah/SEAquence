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
            @RequestPart(value = "avatarRole", required = false) String avatarRole
    ) {
        RealtimeAnalysisResponse response = realtimeAnalysisService.analyzeRealtimeAudio(file, avatarRole);
        return ResponseEntity.ok(response);
    }
}