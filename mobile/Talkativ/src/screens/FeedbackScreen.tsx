import React, { useState } from 'react';
import {
  View, Text, StyleSheet, SafeAreaView,
  ScrollView, TouchableOpacity,
} from 'react-native';
import { useNavigation, useRoute } from '@react-navigation/native';
import { Star, Clock, MessageCircle, TrendingUp } from 'lucide-react-native';
import { Header, Card, Button, Icon } from '../components';

export default function FeedbackScreen() {
  const navigation = useNavigation<any>();
  const route = useRoute<any>();
  const { avatar, duration, situation } = route.params || {};

  const [rating, setRating] = useState(0);
  const [selectedTags, setSelectedTags] = useState<string[]>([]);

  const feedbackTags = [
    '자연스러웠어요', '도움이 됐어요', '재미있었어요',
    '어려웠어요', '더 연습이 필요해요', '말투가 어색했어요',
  ];

  const toggleTag = (tag: string) => {
    if (selectedTags.includes(tag)) {
      setSelectedTags(selectedTags.filter((t) => t !== tag));
    } else {
      setSelectedTags([...selectedTags, tag]);
    }
  };

  const handleContinue = () => {
    navigation.navigate('Analytics', {
      avatar,
      duration,
      rating,
      feedbackTags: selectedTags,
    });
  };

  return (
    <SafeAreaView style={styles.safe}>
      <Header title="대화 완료" showBack={false} />

      <ScrollView contentContainerStyle={styles.content} showsVerticalScrollIndicator={false}>

        {/* Completion Card */}
        <Card variant="elevated" style={styles.completionCard}>
          <View style={styles.avatarCircle}>
            <View style={[styles.avatarIcon, { backgroundColor: avatar?.avatarBg || '#FFB6C1' }]}>
              <Icon name={avatar?.icon || 'user'} size={32} color="#FFFFFF" />
            </View>
          </View>
          <Text style={styles.completionTitle}>대화를 완료했어요!</Text>
          <Text style={styles.completionSubtitle}>
            {avatar?.name_ko || '아바타'}와의 대화가 끝났습니다
          </Text>
        </Card>

        {/* Stats */}
        <View style={styles.statsRow}>
          <Card variant="elevated" style={styles.statCard}>
            <Clock size={24} color="#6C3BFF" />
            <Text style={styles.statValue}>{duration || '05:00'}</Text>
            <Text style={styles.statLabel}>대화 시간</Text>
          </Card>
          <Card variant="elevated" style={styles.statCard}>
            <MessageCircle size={24} color="#F4A261" />
            <Text style={styles.statValue}>12</Text>
            <Text style={styles.statLabel}>메시지</Text>
          </Card>
          <Card variant="elevated" style={styles.statCard}>
            <TrendingUp size={24} color="#4CAF50" />
            <Text style={styles.statValue}>85%</Text>
            <Text style={styles.statLabel}>정확도</Text>
          </Card>
        </View>

        {/* Rating */}
        <Text style={styles.sectionTitle}>대화는 어땠나요?</Text>
        <View style={styles.ratingRow}>
          {[1, 2, 3, 4, 5].map((star) => (
            <TouchableOpacity
              key={star}
              onPress={() => setRating(star)}
              style={styles.starButton}
            >
              <Star
                size={36}
                color={star <= rating ? '#F4A261' : '#E2E2EC'}
                fill={star <= rating ? '#F4A261' : 'transparent'}
              />
            </TouchableOpacity>
          ))}
        </View>
        <Text style={styles.ratingText}>
          {rating === 0 && '별점을 선택해주세요'}
          {rating === 1 && '아쉬웠어요 😔'}
          {rating === 2 && '그저 그랬어요 😐'}
          {rating === 3 && '괜찮았어요 🙂'}
          {rating === 4 && '좋았어요! 😊'}
          {rating === 5 && '최고였어요! 🎉'}
        </Text>

        {/* Feedback Tags */}
        <Text style={styles.sectionTitle}>어떤 점이 좋았나요? (선택)</Text>
        <View style={styles.tagsContainer}>
          {feedbackTags.map((tag) => (
            <TouchableOpacity
              key={tag}
              style={[
                styles.feedbackTag,
                selectedTags.includes(tag) && styles.feedbackTagSelected,
              ]}
              onPress={() => toggleTag(tag)}
            >
              <Text style={[
                styles.feedbackTagText,
                selectedTags.includes(tag) && styles.feedbackTagTextSelected,
              ]}>
                {tag}
              </Text>
            </TouchableOpacity>
          ))}
        </View>

      </ScrollView>

      {/* Continue Button */}
      <View style={styles.footer}>
        <Button
          title="분석 결과 보기"
          onPress={handleContinue}
          showArrow
          disabled={rating === 0}
        />
      </View>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safe: { flex: 1, backgroundColor: '#F7F7FB' },
  content: { paddingHorizontal: 20, paddingBottom: 100 },

  // Completion Card
  completionCard: {
    alignItems: 'center',
    paddingVertical: 32,
    marginBottom: 20,
  },
  avatarCircle: {
    marginBottom: 16,
  },
  avatarIcon: {
    width: 72,
    height: 72,
    borderRadius: 36,
    alignItems: 'center',
    justifyContent: 'center',
  },
  completionTitle: {
    fontSize: 22,
    fontWeight: '700',
    color: '#1A1A2E',
    marginBottom: 4,
  },
  completionSubtitle: {
    fontSize: 14,
    color: '#6C6C80',
  },

  // Stats
  statsRow: {
    flexDirection: 'row',
    gap: 12,
    marginBottom: 28,
  },
  statCard: {
    flex: 1,
    alignItems: 'center',
    paddingVertical: 16,
  },
  statValue: {
    fontSize: 20,
    fontWeight: '700',
    color: '#1A1A2E',
    marginTop: 8,
    marginBottom: 2,
  },
  statLabel: {
    fontSize: 11,
    color: '#6C6C80',
  },

  // Section
  sectionTitle: {
    fontSize: 16,
    fontWeight: '700',
    color: '#1A1A2E',
    marginBottom: 16,
  },

  // Rating
  ratingRow: {
    flexDirection: 'row',
    justifyContent: 'center',
    gap: 8,
    marginBottom: 12,
  },
  starButton: {
    padding: 4,
  },
  ratingText: {
    textAlign: 'center',
    fontSize: 14,
    color: '#6C6C80',
    marginBottom: 28,
  },

  // Tags
  tagsContainer: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 10,
  },
  feedbackTag: {
    paddingHorizontal: 16,
    paddingVertical: 10,
    borderRadius: 20,
    backgroundColor: '#FFFFFF',
    borderWidth: 1.5,
    borderColor: '#E2E2EC',
  },
  feedbackTagSelected: {
    backgroundColor: '#6C3BFF',
    borderColor: '#6C3BFF',
  },
  feedbackTagText: {
    fontSize: 13,
    color: '#6C6C80',
  },
  feedbackTagTextSelected: {
    color: '#FFFFFF',
    fontWeight: '600',
  },

  // Footer
  footer: {
    position: 'absolute',
    bottom: 0,
    left: 0,
    right: 0,
    padding: 20,
    backgroundColor: '#F7F7FB',
  },
});
