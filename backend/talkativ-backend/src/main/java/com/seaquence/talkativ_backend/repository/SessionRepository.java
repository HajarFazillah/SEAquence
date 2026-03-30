package com.seaquence.talkativ_backend.repository;

import com.seaquence.talkativ_backend.entity.Session;
import org.springframework.data.jpa.repository.JpaRepository;
import java.util.List;

public interface SessionRepository extends JpaRepository<Session, String> {
    List<Session> findByUserIdAndStatus(String userId, String status);
}