package com.seaquence.talkativ_backend.controller;

import com.seaquence.talkativ_backend.entity.Vocabulary;
import com.seaquence.talkativ_backend.repository.VocabularyRepository;
import org.springframework.http.ResponseEntity;
import org.springframework.security.core.Authentication;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.bind.annotation.*;

import java.util.ArrayList;
import java.util.List;
import java.util.Optional;

@RestController
@RequestMapping(value = "/api/vocabulary", produces = "application/json;charset=UTF-8")
@CrossOrigin(origins = "*")
public class VocabularyController {

    private final VocabularyRepository repo;

    public VocabularyController(VocabularyRepository repo) {
        this.repo = repo;
    }

    public static class VocabularyItem {
        public String kind;            // 'word' | 'phrase'
        public String word;
        public String meaning;
        public String example;
        public String fromAvatar;
        public String sessionId;

        public String getKind() { return kind; }
        public void setKind(String kind) { this.kind = kind; }
        public String getWord() { return word; }
        public void setWord(String word) { this.word = word; }
        public String getMeaning() { return meaning; }
        public void setMeaning(String meaning) { this.meaning = meaning; }
        public String getExample() { return example; }
        public void setExample(String example) { this.example = example; }
        public String getFromAvatar() { return fromAvatar; }
        public void setFromAvatar(String fromAvatar) { this.fromAvatar = fromAvatar; }
        public String getSessionId() { return sessionId; }
        public void setSessionId(String sessionId) { this.sessionId = sessionId; }
    }

    public static class SaveRequest {
        public List<VocabularyItem> items;

        public List<VocabularyItem> getItems() { return items; }
        public void setItems(List<VocabularyItem> items) { this.items = items; }
    }

    private String resolveUserId(Authentication auth) {
        if (auth != null && auth.getPrincipal() != null) {
            return (String) auth.getPrincipal();
        }
        return "anonymous";
    }

    @PostMapping
    public ResponseEntity<List<Vocabulary>> save(
            @RequestBody SaveRequest request,
            Authentication auth) {

        String userId = resolveUserId(auth);
        List<Vocabulary> saved = new ArrayList<>();
        if (request.getItems() == null || request.getItems().isEmpty()) {
            return ResponseEntity.ok(saved);
        }

        for (VocabularyItem item : request.getItems()) {
            if (item.word == null || item.word.isBlank()) continue;
            String kind = (item.kind == null || item.kind.isBlank()) ? "word" : item.kind;

            // Upsert: avoid duplicate (user, kind, word) entries
            Optional<Vocabulary> existing = repo.findByUserIdAndKindAndWord(userId, kind, item.word);
            Vocabulary v = existing.orElseGet(Vocabulary::new);
            v.setUserId(userId);
            v.setKind(kind);
            v.setWord(item.word);
            v.setMeaning(item.meaning);
            v.setExample(item.example);
            v.setFromAvatar(item.fromAvatar);
            v.setSessionId(item.sessionId);
            saved.add(repo.save(v));
        }
        return ResponseEntity.ok(saved);
    }

    @GetMapping("/me")
    public ResponseEntity<List<Vocabulary>> listMine(
            @RequestParam(value = "kind", required = false) String kind,
            Authentication auth) {

        String userId = resolveUserId(auth);
        List<Vocabulary> rows = (kind == null || kind.isBlank())
                ? repo.findByUserIdOrderByCreatedAtDesc(userId)
                : repo.findByUserIdAndKindOrderByCreatedAtDesc(userId, kind);
        return ResponseEntity.ok(rows);
    }

    @DeleteMapping("/me")
    @Transactional
    public ResponseEntity<Void> deleteAll(Authentication auth) {
        String userId = resolveUserId(auth);
        repo.deleteByUserId(userId);
        return ResponseEntity.noContent().build();
    }

    @DeleteMapping("/{id}")
    public ResponseEntity<Void> delete(@PathVariable Long id, Authentication auth) {
        String userId = resolveUserId(auth);
        repo.findById(id).ifPresent(v -> {
            // Only allow deleting your own row
            if (userId.equals(v.getUserId())) {
                repo.deleteById(id);
            }
        });
        return ResponseEntity.noContent().build();
    }
}
