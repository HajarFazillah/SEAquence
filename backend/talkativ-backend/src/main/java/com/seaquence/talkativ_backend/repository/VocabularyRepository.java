package com.seaquence.talkativ_backend.repository;

import com.seaquence.talkativ_backend.entity.Vocabulary;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.List;
import java.util.Optional;

public interface VocabularyRepository extends JpaRepository<Vocabulary, Long> {
    List<Vocabulary> findByUserIdOrderByCreatedAtDesc(String userId);
    List<Vocabulary> findByUserIdAndKindOrderByCreatedAtDesc(String userId, String kind);
    Optional<Vocabulary> findByUserIdAndKindAndWord(String userId, String kind, String word);
    void deleteByUserId(String userId);
}
