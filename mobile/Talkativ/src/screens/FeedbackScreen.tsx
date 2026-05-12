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

  const finalTurns = useMemo(
    () =>
      (turns || []).filter(
        (turn: TranscriptTurn) => turn.type !== 'partial' && !!turn.text?.trim()
      ),
    [turns]
  );

  const stats = useMemo(() => {
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
  }, [finalTurns, insights]);

  const summaryCopy = useMemo(() => {
    if (stats.qualityScore >= 90) {
      return '대화 흐름이 자연스럽고 안정적으로 이어졌어요.';
    }
    if (stats.qualityScore >= 75) {
      return '좋은 흐름으로 마무리됐어요. 핵심 포인트도 잘 잡혔어요.';
    }
    if (stats.qualityScore >= 60) {
      return '전체 흐름은 괜찮았고, 몇 가지 포인트를 더 다듬으면 더 좋아져요.';
    }
    return '이번 대화를 바탕으로 다음 연습에서 더 분명하게 개선할 수 있어요.';
  }, [stats.qualityScore]);

  const statsCards = useMemo(
    () => [
      {
        key: 'duration',
        icon: Clock,
        color: '#6C3BFF',
        value: duration || '00:00',
        label: '대화 시간',
      },
      {
        key: 'turns',
        icon: MessageCircle,
        color: '#F4A261',
        value: String(stats.messageCount),
        label: '대화 턴 수',
      },
      {
        key: 'score',
        icon: TrendingUp,
        color: '#22C55E',
        value: `${stats.qualityScore}%`,
        label: '세션 점수',
      },
    ],
    [duration, stats.messageCount, stats.qualityScore]
  );

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
          <View style={styles.heroRow}>
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

            <View style={styles.heroTextWrap}>
              <Text style={styles.eyebrow}>SESSION COMPLETE</Text>
              <Text style={styles.completionTitle}>대화를 완료했어요!</Text>
              <Text style={styles.completionSubtitle}>
                {avatar?.name_ko || '아바타'}와의 세션이 끝났습니다
              </Text>
            </View>
          </View>

          <View style={styles.heroSummaryBox}>
            <Text style={styles.heroSummaryText}>{summaryCopy}</Text>
          </View>

          {situation ? (
            <View style={styles.situationPill}>
              <Sparkles size={14} color="#6C3BFF" />
              <Text style={styles.situationText}>{situation}</Text>
            </View>
          ) : null}
        </Card>

        {/* ── Session stats ── */}
        <View style={styles.statsRow}>
          {statsCards.map((item) => {
            const StatIcon = item.icon;
            return (
              <Card key={item.key} variant="elevated" style={styles.statCard}>
                <View style={[styles.statIconWrap, { backgroundColor: `${item.color}16` }]}>
                  <StatIcon size={20} color={item.color} />
                </View>
                <Text style={styles.statValue}>{item.value}</Text>
                <Text style={styles.statLabel}>{item.label}</Text>
              </Card>
            );
          })}
        </View>

        {/* ── Transcript preview ── */}
        <Text style={styles.sectionTitle}>인식된 대화</Text>
        <Card variant="elevated" style={styles.transcriptCard}>
          {finalTurns.length > 0 ? (
            finalTurns.map((turn: TranscriptTurn, index: number) => (
              <View
                key={turn.id || `${turn.speaker}-${index}`}
                style={[
                  styles.transcriptRow,
                  index !== finalTurns.length - 1 && styles.transcriptRowBorder,
                ]}
              >
                <Text style={styles.transcriptSpeaker}>{turn.speaker || '나'}</Text>
                <Text style={styles.transcriptText}>{turn.text}</Text>
              </View>
            ))
          ) : (
            <View style={styles.transcriptEmpty}>
              <Text style={styles.transcriptEmptyTitle}>아직 표시할 transcript가 없어요.</Text>
              <Text style={styles.transcriptEmptyText}>
                음성이 인식되지 않았거나, 이 세션에서 전달된 대화 기록이 없을 수 있어요.
              </Text>
            </View>
          )}
        </Card>

        {/* ── Insight summary ── */}
        {!!insights?.length && (
          <>
            <Text style={styles.sectionTitle}>세션 인사이트</Text>
            <Card variant="elevated" style={styles.insightSummaryCard}>
              <Text style={styles.insightSummaryTitle}>이번 세션의 흐름</Text>
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
    paddingVertical: 24,
    paddingHorizontal: 20,
    marginBottom: 20,
  },
  heroRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 16,
    marginBottom: 18,
  },
  heroTextWrap: {
    flex: 1,
  },
  avatarCircle: {
    alignSelf: 'flex-start',
  },
  avatarIcon: {
    width: 72,
    height: 72,
    borderRadius: 36,
    alignItems: 'center',
    justifyContent: 'center',
  },
  eyebrow: {
    fontSize: 11,
    fontWeight: '700',
    letterSpacing: 1,
    color: '#8E8EA9',
    marginBottom: 6,
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
    lineHeight: 20,
  },
  heroSummaryBox: {
    borderRadius: 18,
    backgroundColor: '#F6F3FF',
    paddingHorizontal: 16,
    paddingVertical: 14,
    marginBottom: 14,
  },
  heroSummaryText: {
    fontSize: 13,
    lineHeight: 20,
    color: '#5B4C8A',
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
    paddingVertical: 18,
    paddingHorizontal: 10,
  },
  statIconWrap: {
    width: 42,
    height: 42,
    borderRadius: 21,
    alignItems: 'center',
    justifyContent: 'center',
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

  transcriptCard: {
    paddingVertical: 8,
    paddingHorizontal: 16,
    marginBottom: 28,
  },
  transcriptRow: {
    paddingVertical: 14,
    gap: 6,
  },
  transcriptRowBorder: {
    borderBottomWidth: 1,
    borderBottomColor: '#EFEFF5',
  },
  transcriptSpeaker: {
    fontSize: 11,
    fontWeight: '700',
    letterSpacing: 0.6,
    color: '#8E8EA9',
  },
  transcriptText: {
    fontSize: 15,
    lineHeight: 22,
    color: '#1A1A2E',
  },
  transcriptEmpty: {
    paddingVertical: 18,
    gap: 6,
  },
  transcriptEmptyTitle: {
    fontSize: 14,
    fontWeight: '600',
    color: '#6C6C80',
  },
  transcriptEmptyText: {
    fontSize: 13,
    lineHeight: 20,
    color: '#9E9EAE',
  },

  insightSummaryCard: {
    paddingVertical: 18,
    paddingHorizontal: 14,
    marginBottom: 28,
  },
  insightSummaryTitle: {
    fontSize: 13,
    fontWeight: '700',
    color: '#6C6C80',
    marginBottom: 14,
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
