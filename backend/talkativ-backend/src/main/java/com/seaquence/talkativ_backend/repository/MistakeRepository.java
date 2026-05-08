package com.seaquence.talkativ_backend.repository;

import com.seaquence.talkativ_backend.entity.Mistake;
import org.springframework.data.jpa.repository.JpaRepository;
import java.util.List;

public interface MistakeRepository extends JpaRepository<Mistake, Long> {
    List<Mistake> findBySessionId(String sessionId);
    List<Mistake> findByUserId(String userId);
    List<Mistake> findByUserIdOrderByCreatedAtDesc(String userId);
    List<Mistake> findBySessionIdOrderByTurnNumberAsc(String sessionId);
}
