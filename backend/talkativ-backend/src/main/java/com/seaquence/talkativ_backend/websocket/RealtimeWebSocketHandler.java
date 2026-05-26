package com.seaquence.talkativ_backend.websocket;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.seaquence.talkativ_backend.dto.RealtimeAnalysisResponse;
import com.seaquence.talkativ_backend.service.RealtimeAnalysisService;
import org.springframework.stereotype.Component;
import org.springframework.web.socket.CloseStatus;
import org.springframework.web.socket.TextMessage;
import org.springframework.web.socket.WebSocketSession;
import org.springframework.web.socket.handler.TextWebSocketHandler;

import java.util.ArrayList;
import java.util.Base64;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

@Component
public class RealtimeWebSocketHandler extends TextWebSocketHandler {

    private final RealtimeAnalysisService realtimeAnalysisService;
    private final ObjectMapper objectMapper = new ObjectMapper();

    public RealtimeWebSocketHandler(RealtimeAnalysisService realtimeAnalysisService) {
        this.realtimeAnalysisService = realtimeAnalysisService;
    }

    @Override
    public void afterConnectionEstablished(WebSocketSession session) {
        System.out.println("[WS] Connected: " + session.getId());
    }

    @Override
    protected void handleTextMessage(WebSocketSession session, TextMessage message) throws Exception {
        JsonNode payload = objectMapper.readTree(message.getPayload());

        String audioBase64      = payload.path("audio").asText();
        String sessionId        = payload.path("sessionId").asText(null);
        String userId           = payload.path("userId").asText("anonymous");
        String avatarRole       = payload.path("avatarRole").asText(null);
        String avatarName       = payload.path("avatarName").asText(null);
        String speechLevel      = payload.path("expectedSpeechLevel").asText("polite");
        String chunkIndex       = payload.path("chunkIndex").asText("0");
        String filename         = "chunk-" + chunkIndex + ".m4a";

        JsonNode avatarNode     = payload.path("avatar");
        JsonNode scenarioNode   = payload.path("scenario");

        List<Map<String, String>> conversationHistory = new ArrayList<>();
        JsonNode historyNode = payload.path("conversationHistory");
        if (historyNode.isArray()) {
            for (JsonNode item : historyNode) {
                Map<String, String> turn = new HashMap<>();
                turn.put("speaker", item.path("speaker").asText(""));
                turn.put("text", item.path("text").asText(""));
                conversationHistory.add(turn);
            }
        }

        byte[] audioData = Base64.getDecoder().decode(audioBase64);

        RealtimeAnalysisResponse result = realtimeAnalysisService.analyzeRealtimeAudio(
                audioData, filename, avatarRole, avatarName, userId, sessionId,
                speechLevel, null, chunkIndex, conversationHistory,
                avatarNode.isMissingNode() ? null : avatarNode.toString(),
                scenarioNode.isMissingNode() ? null : scenarioNode.toString()
        );

        session.sendMessage(new TextMessage(objectMapper.writeValueAsString(result)));
    }

    @Override
    public void afterConnectionClosed(WebSocketSession session, CloseStatus status) {
        System.out.println("[WS] Disconnected: " + session.getId() + " — " + status);
    }

    @Override
    public void handleTransportError(WebSocketSession session, Throwable exception) throws Exception {
        System.err.println("[WS] Error on " + session.getId() + ": " + exception.getMessage());
        if (session.isOpen()) session.close(CloseStatus.SERVER_ERROR);
    }
}
