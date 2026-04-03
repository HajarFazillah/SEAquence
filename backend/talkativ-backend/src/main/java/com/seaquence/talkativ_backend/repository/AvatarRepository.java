package com.seaquence.talkativ_backend.repository;

import com.seaquence.talkativ_backend.entity.Avatar;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.List;

@Repository
public interface AvatarRepository extends JpaRepository<Avatar, Long> {
    List<Avatar> findByUserId(String userId);
    void deleteByUserId(String userId);
}
