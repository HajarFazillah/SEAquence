package com.seaquence.talkativ_backend.service;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.core.io.ByteArrayResource;
import org.springframework.http.*;
import org.springframework.http.client.SimpleClientHttpRequestFactory;
import org.springframework.stereotype.Service;
import org.springframework.util.LinkedMultiValueMap;
import org.springframework.util.MultiValueMap;
import org.springframework.web.client.HttpStatusCodeException;
import org.springframework.web.client.RestTemplate;
import org.springframework.web.multipart.MultipartFile;

import java.util.ArrayList;
import java.util.List;

@Service
public class ClovaSpeechService {

    @Value("${clova.speech.url}")
    private String clovaSpeechUrl;

    @Value("${clova.speech.secret}")
    private String clovaSpeechSecret;

    private final RestTemplate restTemplate;
    private final ObjectMapper objectMapper = new ObjectMapper();

    public ClovaSpeechService() {
        this.restTemplate = new RestTemplate();
        this.restTemplate.setRequestFactory(new SimpleClientHttpRequestFactory());
    }

    public ClovaSpeechResult transcribeWithDiarization(MultipartFile file) {
        try {
            if (file == null || file.isEmpty()) {
                throw new IllegalArgumentException("Audio file is empty.");
            }

            HttpHeaders headers = new HttpHeaders();
            headers.setContentType(MediaType.MULTIPART_FORM_DATA);
            headers.set("X-CLOVASPEECH-API-KEY", clovaSpeechSecret);

            MultiValueMap<String, Object> body = new LinkedMultiValueMap<>();

            ByteArrayResource fileResource = new ByteArrayResource(file.getBytes()) {
                @Override
                public String getFilename() {
                    return file.getOriginalFilename() != null ? file.getOriginalFilename() : "audio.m4a";
                }
            };

            HttpHeaders mediaHeaders = new HttpHeaders();
            mediaHeaders.setContentType(MediaType.APPLICATION_OCTET_STREAM);
            HttpEntity<ByteArrayResource> mediaPart = new HttpEntity<>(fileResource, mediaHeaders);
            body.add("media", mediaPart);

            HttpHeaders paramsHeaders = new HttpHeaders();
            paramsHeaders.setContentType(MediaType.APPLICATION_JSON);

            String paramsJson = """
                {
                  "language": "ko-KR",
                  "completion": "sync",
                  "diarization": {
                    "enable": false
                  }
                }
                """;

            HttpEntity<String> paramsPart = new HttpEntity<>(paramsJson, paramsHeaders);
            body.add("params", paramsPart);

            HttpEntity<MultiValueMap<String, Object>> requestEntity = new HttpEntity<>(body, headers);

            ResponseEntity<String> response = restTemplate.exchange(
                    clovaSpeechUrl,
                    HttpMethod.POST,
                    requestEntity,
                    String.class
            );

            System.out.println("CLOVA raw response: " + response.getBody());
            return parseResponse(response.getBody());
        } catch (HttpStatusCodeException e) {
            System.err.println("CLOVA status: " + e.getStatusCode());
            System.err.println("CLOVA body: " + e.getResponseBodyAsString());
            throw new RuntimeException(
                    "Failed to transcribe audio with CLOVA Speech: " + e.getResponseBodyAsString(),
                    e
            );
        } catch (Exception e) {
            throw new RuntimeException("Failed to transcribe audio with CLOVA Speech", e);
        }
    }

    private ClovaSpeechResult parseResponse(String responseBody) {
        try {
            JsonNode root = objectMapper.readTree(responseBody);
            List<SpeakerTurn> turns = new ArrayList<>();

            JsonNode segments = root.path("segments");
            if (segments.isArray()) {
                for (JsonNode segment : segments) {
                    String speaker = segment.path("speaker").path("label").asText("");
                    String text = segment.path("text").asText("");
                    double start = segment.path("start").asDouble(0);
                    double end = segment.path("end").asDouble(0);

                    turns.add(new SpeakerTurn(speaker, text, start, end));
                }
            }

            String fullText = root.path("text").asText("");
            return new ClovaSpeechResult(fullText, turns);
        } catch (Exception e) {
            throw new RuntimeException("Failed to parse CLOVA Speech response", e);
        }
    }

    public static class ClovaSpeechResult {
        private final String fullText;
        private final List<SpeakerTurn> turns;

        public ClovaSpeechResult(String fullText, List<SpeakerTurn> turns) {
            this.fullText = fullText;
            this.turns = turns;
        }

        public String getFullText() {
            return fullText;
        }

        public List<SpeakerTurn> getTurns() {
            return turns;
        }
    }

    public static class SpeakerTurn {
        private final String speaker;
        private final String text;
        private final double start;
        private final double end;

        public SpeakerTurn(String speaker, String text, double start, double end) {
            this.speaker = speaker;
            this.text = text;
            this.start = start;
            this.end = end;
        }

        public String getSpeaker() {
            return speaker;
        }

        public String getText() {
            return text;
        }

        public double getStart() {
            return start;
        }

        public double getEnd() {
            return end;
        }
    }
}
