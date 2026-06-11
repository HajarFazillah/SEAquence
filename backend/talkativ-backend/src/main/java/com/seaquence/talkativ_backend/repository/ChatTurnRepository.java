package com.seaquence.talkativ_backend.repository;

import com.seaquence.talkativ_backend.entity.ChatTurn;
import org.springframework.data.jpa.repository.JpaRepository;
import java.util.List;

public interface ChatTurnRepository extends JpaRepository<ChatTurn, Long> {
    List<ChatTurn> findBySessionIdOrderByTurnNumberAsc(String sessionId);
    void deleteBySessionId(String sessionId);
}
