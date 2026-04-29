import React, { useMemo, useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useNavigation, useRoute } from '@react-navigation/native';
import {
  Star,
  Clock,
  MessageCircle,
  TrendingUp,
  Sparkles,
} from 'lucide-react-native';
import { Header, Card, Button, Icon } from '../components';
import type { NativeStackScreenProps } from '@react-navigation/native-stack';
import type { RootStackParamList } from '../navigation/AppNavigator';

type FeedbackRoute = NativeStackScreenProps<
  RootStackParamList,
  'Feedback'
>['route'];

type TranscriptTurn = {
  id: string;
  speaker: string;
  text: string;
  type?: 'partial' | 'final';
};

type Insight = {
  id: string;
  kind?: 'risk' | 'success';
  message: string;
  suggestion?: string;
  turnId?: string;
};

const FEEDBACK_TAGS = [
  '자연스러웠어요',
  '도움이 됐어요',
  '재미있었어요',
  '어려웠어요',
  '더 연습이 필요해요',
  '말투가 어색했어요',
] as const;

export default function FeedbackScreen() {
  const navigation = useNavigation<any>();
  const route = useRoute<FeedbackRoute>();

  const {
    avatar,
    duration,
    situation,
    sessionId,
    recordingUri,
    turns = [],
    insights = [],
  } = route.params || {};

  const [rating, setRating] = useState(0);
  const [selectedTags, setSelectedTags] = useState<string[]>([]);

  const stats = useMemo(() => {
    const finalTurns: TranscriptTurn[] = (turns || []).filter(
      (turn: TranscriptTurn) => turn.type !== 'partial'
    );

    const messageCount = finalTurns.length;

    const successCount = (insights || []).filter(
      (insight: Insight) => insight.kind === 'success'
    ).length;

    const riskCount = (insights || []).filter(
      (insight: Insight) => insight.kind === 'risk'
    ).length;

    const speakerCount = new Set(
      finalTurns.map((turn: TranscriptTurn) => turn.speaker).filter(Boolean)
    ).size;

    let score = 70;
    if (messageCount >= 6) score += 8;
    if (messageCount >= 12) score += 6;
    if (speakerCount >= 2) score += 4;
    if (successCount > 0) score += Math.min(successCount * 3, 12);
    if (riskCount > 0) score -= Math.min(riskCount * 4, 16);

    const qualityScore = Math.max(45, Math.min(98, score));

    return { messageCount, successCount, riskCount, speakerCount, qualityScore };
  }, [turns, insights]);

  const toggleTag = (tag: string) => {
    setSelectedTags((prev) =>
      prev.includes(tag) ? prev.filter((t) => t !== tag) : [...prev, tag]
    );
  };

  const handleContinue = () => {
    navigation.navigate('Analytics', {
      avatar,
      duration,
      situation,
      sessionId,
      recordingUri,
      rating,
      feedbackTags: selectedTags,
      turns,
      insights,
      stats,
    });
  };

  const ratingText = useMemo(() => {
    if (rating === 0) return '별점을 선택해주세요';
    if (rating === 1) return '아쉬웠어요';
    if (rating === 2) return '그저 그랬어요';
    if (rating === 3) return '괜찮았어요';
    if (rating === 4) return '좋았어요!';
    return '최고였어요!';
  }, [rating]);

  return (
    <SafeAreaView style={styles.safe} edges={['top']}>
      <Header title="대화 완료" showBack={false} />

      <ScrollView
        contentContainerStyle={styles.content}
        showsVerticalScrollIndicator={false}
      >
        {/* ── Completion card ── */}
        <Card variant="elevated" style={styles.completionCard}>
          <View style={styles.avatarCircle}>
            <View
              style={[
                styles.avatarIcon,
                { backgroundColor: avatar?.avatar_bg || avatar?.avatarBg || '#FFB6C1' },
              ]}
            >
              <Icon name={avatar?.icon || 'user'} size={32} color="#FFFFFF" />
            </View>
          </View>

          <Text style={styles.completionTitle}>대화를 완료했어요!</Text>
          <Text style={styles.completionSubtitle}>
            {avatar?.name_ko || '아바타'}와의 세션이 끝났습니다
          </Text>

          {situation ? (
            <View style={styles.situationPill}>
              <Sparkles size={14} color="#6C3BFF" />
              <Text style={styles.situationText}>{situation}</Text>
            </View>
          ) : null}
        </Card>

        {/* ── Session stats ── */}
        <View style={styles.statsRow}>
          <Card variant="elevated" style={styles.statCard}>
            <Clock size={24} color="#6C3BFF" />
            <Text style={styles.statValue}>{duration || '00:00'}</Text>
            <Text style={styles.statLabel}>대화 시간</Text>
          </Card>

          <Card variant="elevated" style={styles.statCard}>
            <MessageCircle size={24} color="#F4A261" />
            <Text style={styles.statValue}>{stats.messageCount}</Text>
            <Text style={styles.statLabel}>Transcript turns</Text>
          </Card>

          <Card variant="elevated" style={styles.statCard}>
            <TrendingUp size={24} color="#4CAF50" />
            <Text style={styles.statValue}>{stats.qualityScore}%</Text>
            <Text style={styles.statLabel}>세션 점수</Text>
          </Card>
        </View>

        {/* ── Insight summary ── */}
        {!!insights?.length && (
          <>
            <Text style={styles.sectionTitle}>세션 인사이트</Text>
            <Card variant="elevated" style={styles.insightSummaryCard}>
              <View style={styles.insightSummaryRow}>
                <View style={styles.insightMetric}>
                  <Text style={styles.insightMetricValue}>{stats.successCount}</Text>
                  <Text style={styles.insightMetricLabel}>긍정 신호</Text>
                </View>
                <View style={styles.insightMetricDivider} />
                <View style={styles.insightMetric}>
                  <Text style={styles.insightMetricValue}>{stats.riskCount}</Text>
                  <Text style={styles.insightMetricLabel}>주의 포인트</Text>
                </View>
                <View style={styles.insightMetricDivider} />
                <View style={styles.insightMetric}>
                  <Text style={styles.insightMetricValue}>{stats.speakerCount}</Text>
                  <Text style={styles.insightMetricLabel}>화자 수</Text>
                </View>
              </View>
            </Card>
          </>
        )}

        {/* ── Star rating ── */}
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
        <Text style={styles.ratingText}>{ratingText}</Text>

        {/* ── Feedback tags ── */}
        <Text style={styles.sectionTitle}>어떤 점이 좋았나요? (선택)</Text>
        <View style={styles.tagsContainer}>
          {FEEDBACK_TAGS.map((tag) => (
            <TouchableOpacity
              key={tag}
              style={[
                styles.feedbackTag,
                selectedTags.includes(tag) && styles.feedbackTagSelected,
              ]}
              onPress={() => toggleTag(tag)}
            >
              <Text
                style={[
                  styles.feedbackTagText,
                  selectedTags.includes(tag) && styles.feedbackTagTextSelected,
                ]}
              >
                {tag}
              </Text>
            </TouchableOpacity>
          ))}
        </View>
      </ScrollView>

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
    marginBottom: 14,
  },
  situationPill: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    paddingHorizontal: 12,
    paddingVertical: 8,
    borderRadius: 20,
    backgroundColor: '#F0EDFF',
  },
  situationText: {
    fontSize: 12,
    fontWeight: '600',
    color: '#6C3BFF',
  },

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
    textAlign: 'center',
  },

  sectionTitle: {
    fontSize: 16,
    fontWeight: '700',
    color: '#1A1A2E',
    marginBottom: 16,
  },

  insightSummaryCard: {
    paddingVertical: 18,
    paddingHorizontal: 14,
    marginBottom: 28,
  },
  insightSummaryRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
  },
  insightMetric: {
    flex: 1,
    alignItems: 'center',
  },
  insightMetricValue: {
    fontSize: 20,
    fontWeight: '700',
    color: '#6C3BFF',
    marginBottom: 4,
  },
  insightMetricLabel: {
    fontSize: 12,
    color: '#6C6C80',
  },
  insightMetricDivider: {
    width: 1,
    height: 36,
    backgroundColor: '#EAEAF2',
  },

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

  footer: {
    position: 'absolute',
    bottom: 0,
    left: 0,
    right: 0,
    padding: 20,
    backgroundColor: '#F7F7FB',
  },
});