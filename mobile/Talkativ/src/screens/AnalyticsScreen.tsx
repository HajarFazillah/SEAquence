import React, { useEffect, useMemo, useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  ActivityIndicator,
  TouchableOpacity,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useNavigation, useRoute } from '@react-navigation/native';
import {
  TrendingUp,
  AlertCircle,
  BookOpen,
  MessageCircle,
  Target,
  ChevronLeft,
  Sparkles,
  AlertTriangle,
  CheckCircle2,
  Star,
} from 'lucide-react-native';
import { Tag } from '../components';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { AI_SERVER_URL } from '../constants';

const AI_SERVER = AI_SERVER_URL;

// ─── Types ────────────────────────────────────────────────────────────────────

interface AnalyticsSummary {
  overall_score: number;
  proficiency_level_ko: string;
  current_streak: number;
  streak_emoji: string;
  weekly_change: number;
  total_vocabulary: number;
  total_conversations: number;
}

interface WeakArea {
  error_type: string;
  error_type_ko: string;
  count: number;
  severity: string;
}

interface ScoreDetail {
  source?: string;
  used_fallback?: boolean;
  note?: string;
}

interface TranscriptTurn {
  id: string;
  speaker: string;
  text: string;
  type?: 'partial' | 'final';
}

interface Insight {
  id: string;
  kind: 'risk' | 'success';
  message: string;
  suggestion?: string;
  turnId?: string;
}

interface SessionStats {
  messageCount: number;
  successCount: number;
  riskCount: number;
  speakerCount: number;
  qualityScore: number;
}

// ─── Helpers ──────────────────────────────────────────────────────────────────

const getHeroColor = (score: number): string => {
  if (score >= 85) return '#22C55E';
  if (score >= 70) return '#6C3BFF';
  return '#FF4D4D';
};

const getWeakAreaColor = (severity: string, index: number): string => {
  if (severity === 'high' || severity === 'error') return '#FF4D4D';
  if (severity === 'medium' || severity === 'warning') return '#EAB308';
  return ['#6C3BFF', '#3F51B5', '#009688'][index % 3];
};

const getHeroLabel = (score: number): string => {
  if (score >= 85) return '아주 잘 하고 있어요';
  if (score >= 70) return '꾸준히 성장 중';
  return '집중 연습 추천';
};

const clamp01 = (value: number) => Math.max(0, Math.min(1, value));

const buildSessionScores = (
  stats?: SessionStats,
  turns: TranscriptTurn[] = [],
  insights: Insight[] = [],
  rating = 0
) => {
  if (stats) {
    const speechAccuracy = clamp01(stats.qualityScore / 100);

    const vocabularyBase =
      0.58 +
      Math.min(turns.filter((t) => (t.text || '').trim().length > 20).length * 0.03, 0.22) +
      Math.min(stats.successCount * 0.02, 0.12) -
      Math.min(stats.riskCount * 0.025, 0.12);

    const naturalnessBase =
      0.55 +
      Math.min(stats.speakerCount * 0.08, 0.16) +
      Math.min(stats.messageCount * 0.015, 0.16) +
      Math.min(rating * 0.03, 0.15) -
      Math.min(stats.riskCount * 0.02, 0.12);

    return {
      speechAccuracy: clamp01(speechAccuracy),
      vocabulary: clamp01(vocabularyBase),
      naturalness: clamp01(naturalnessBase),
    };
  }

  const finalTurns = turns.filter((turn) => turn.type !== 'partial');
  const successCount = insights.filter((insight) => insight.kind === 'success').length;
  const riskCount = insights.filter((insight) => insight.kind === 'risk').length;
  const speakerCount = new Set(finalTurns.map((turn) => turn.speaker).filter(Boolean)).size || 1;

  const speechAccuracy = clamp01(
    0.68 +
      Math.min(successCount * 0.04, 0.16) -
      Math.min(riskCount * 0.05, 0.18)
  );

  const vocabulary = clamp01(
    0.60 +
      Math.min(finalTurns.filter((t) => (t.text || '').length > 18).length * 0.025, 0.18)
  );

  const naturalness = clamp01(
    0.58 +
      Math.min(speakerCount * 0.08, 0.16) +
      Math.min(rating * 0.04, 0.20) -
      Math.min(riskCount * 0.03, 0.15)
  );

  return { speechAccuracy, vocabulary, naturalness };
};

const getScoreSourceLabel = (detail?: ScoreDetail) => {
  if (!detail?.source) return '';
  if (detail.used_fallback) return '기본값 사용';
  if (detail.source.includes('konlpy')) return 'KoNLPy 보조';
  if (detail.source === 'rule_based') return '규칙 기반 계산';
  return '혼합 계산';
};

// ─── Screen ───────────────────────────────────────────────────────────────────

export default function AnalyticsScreen() {
  const navigation = useNavigation<any>();
  const route = useRoute<any>();

  const {
    avatar,
    duration,
    scores,
    scoreDetails,
    usedFallbackScores,
    savedItems,
    source,
    rating = 0,
    feedbackTags = [],
    sessionId,
    recordingUri,
    turns = [],
    insights = [],
    stats,
  } = route.params || {};

  const isHomeAnalysis = source === 'home' || (!avatar && !duration && !scores && !turns?.length);

  const [loading, setLoading] = useState(true);
  const [summary, setSummary] = useState<AnalyticsSummary | null>(null);
  const [weakAreas, setWeakAreas] = useState<WeakArea[]>([]);

  useEffect(() => {
    loadAnalytics();
  }, []);

  const loadAnalytics = async () => {
    try {
      setLoading(true);
      const userId = (await AsyncStorage.getItem('user_id')) || 'test-user-1';

      const [summaryRes, weakRes] = await Promise.allSettled([
        fetch(`${AI_SERVER}/api/v1/analytics/${userId}/summary`),
        fetch(`${AI_SERVER}/api/v1/analytics/${userId}/weak-areas`),
      ]);

      if (summaryRes.status === 'fulfilled' && summaryRes.value.ok) {
        setSummary(await summaryRes.value.json());
      }

      if (weakRes.status === 'fulfilled' && weakRes.value.ok) {
        const data = await weakRes.value.json();
        setWeakAreas(Array.isArray(data) ? data : []);
      }
    } catch (error) {
      console.error('Analytics load error:', error);
    } finally {
      setLoading(false);
    }
  };

  const sessionScores = useMemo(() => {
    if (scores) {
      return {
        speechAccuracy: scores?.speechAccuracy ?? 0.8,
        vocabulary: scores?.vocabulary ?? 0.72,
        naturalness: scores?.naturalness ?? 0.78,
      };
    }

    return buildSessionScores(stats, turns, insights, rating);
  }, [scores, stats, turns, insights, rating]);

  const derivedScoreDetails: {
    speechAccuracy?: ScoreDetail;
    vocabulary?: ScoreDetail;
    naturalness?: ScoreDetail;
  } = scoreDetails || {
    speechAccuracy: !scores
      ? { source: 'rule_based', note: '세션 qualityScore와 인사이트 기반 추정' }
      : undefined,
    vocabulary: !scores
      ? { source: 'rule_based', note: 'turn 길이 및 세션 참여도 기반 추정' }
      : undefined,
    naturalness: !scores
      ? { source: 'rule_based', note: '화자 수, 평점, risk/success 비율 기반 추정' }
      : undefined,
  };

  const effectiveStats: SessionStats | null = useMemo(() => {
    if (stats) return stats;

    const finalTurns = (turns || []).filter((turn: TranscriptTurn) => turn.type !== 'partial');
    const successCount = (insights || []).filter((insight: Insight) => insight.kind === 'success').length;
    const riskCount = (insights || []).filter((insight: Insight) => insight.kind === 'risk').length;
    const speakerCount = new Set(finalTurns.map((turn: TranscriptTurn) => turn.speaker).filter(Boolean)).size;

    const qualityScore = Math.round(
      ((sessionScores.speechAccuracy + sessionScores.vocabulary + sessionScores.naturalness) / 3) * 100
    );

    return {
      messageCount: finalTurns.length,
      successCount,
      riskCount,
      speakerCount,
      qualityScore,
    };
  }, [stats, turns, insights, sessionScores]);

  const overallScore = Math.round(
    ((sessionScores.speechAccuracy + sessionScores.vocabulary + sessionScores.naturalness) / 3) * 100
  );

  const displayScore = isHomeAnalysis ? Math.round(summary?.overall_score || 0) : overallScore;
  const heroColor = getHeroColor(displayScore);
  const heroLabel = getHeroLabel(displayScore);
  const maxWeakCount = Math.max(1, ...weakAreas.map((a) => a.count || 0));

  const finalTurns = (turns || []).filter((turn: TranscriptTurn) => turn.type !== 'partial');
  const topSuccessInsights = (insights || []).filter((insight: Insight) => insight.kind === 'success').slice(0, 3);
  const topRiskInsights = (insights || []).filter((insight: Insight) => insight.kind === 'risk').slice(0, 3);

  const ratingLabel =
    rating === 1 ? '아쉬웠어요' :
    rating === 2 ? '그저 그랬어요' :
    rating === 3 ? '괜찮았어요' :
    rating === 4 ? '좋았어요!' :
    rating === 5 ? '최고였어요!' :
    '평가 없음';

  if (loading) {
    return (
      <SafeAreaView style={styles.safe} edges={['top']}>
        <View style={styles.header}>
          <TouchableOpacity onPress={() => navigation.goBack()} style={styles.headerBtn}>
            <ChevronLeft size={22} color="#111" />
          </TouchableOpacity>
          <Text style={styles.headerTitle}>{isHomeAnalysis ? '실수 분석' : '분석 결과'}</Text>
          <View style={styles.headerBtn} />
        </View>

        <View style={styles.loadingWrap}>
          <ActivityIndicator size="large" color="#6C3BFF" />
          <Text style={styles.loadingText}>분석 중...</Text>
        </View>
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView style={styles.safe} edges={['top']}>
      <View style={styles.header}>
        <TouchableOpacity onPress={() => navigation.goBack()} style={styles.headerBtn}>
          <ChevronLeft size={22} color="#111" />
        </TouchableOpacity>
        <Text style={styles.headerTitle}>{isHomeAnalysis ? '실수 분석' : '분석 결과'}</Text>
        <View style={styles.headerBtn} />
      </View>

      <ScrollView contentContainerStyle={styles.content} showsVerticalScrollIndicator={false}>
        <View style={[styles.heroCard, { backgroundColor: heroColor }]}>
          <View style={styles.heroBlobA} />
          <View style={styles.heroBlobB} />

          <View style={styles.heroTopRow}>
            <View style={styles.heroPill}>
              <Target size={12} color="#fff" />
              <Text style={styles.heroPillText}>
                {isHomeAnalysis ? 'Mistake Report' : 'Session Report'}
              </Text>
            </View>
            <Text style={styles.heroLabel}>{heroLabel}</Text>
          </View>

          <Text style={styles.heroTitle}>
            {isHomeAnalysis ? '실수 패턴을 한눈에 봐요' : '이번 대화가 이렇게 쌓였어요'}
          </Text>

          <Text style={styles.heroSub}>
            {isHomeAnalysis
              ? '이전 대화의 반복 실수와 다음 연습 방향을 정리합니다.'
              : `${avatar?.name_ko || '아바타'}와 ${duration || '5분'} 동안 연습한 결과입니다.`}
          </Text>

          <View style={styles.heroBottom}>
            <View style={styles.heroScoreBubble}>
              <Text style={[styles.heroScore, { color: heroColor }]}>{displayScore}</Text>
              <Text style={[styles.heroScoreUnit, { color: heroColor }]}>점</Text>
            </View>

            <View style={styles.heroInsight}>
              <Text style={styles.heroInsightEye}>오늘의 포커스</Text>
              <Text style={styles.heroInsightText}>
                {topRiskInsights[0]?.message ||
                  weakAreas[0]?.error_type_ko ||
                  weakAreas[0]?.error_type ||
                  '대화 흐름을 꾸준히 유지해보세요'}
              </Text>
            </View>
          </View>
        </View>

        {summary && (
          <View style={styles.section}>
            <View style={styles.sectionHead}>
              <Text style={styles.sectionEye}>PROGRESS</Text>
              <Text style={styles.sectionTitle}>누적 학습 현황</Text>
            </View>

            <View style={styles.card}>
              <View style={styles.summaryGrid}>
                {[
                  { value: summary.proficiency_level_ko, label: '현재 수준' },
                  { value: `${summary.current_streak}일`, label: '연속 학습' },
                  { value: `${summary.total_conversations}회`, label: '총 대화' },
                  { value: `${summary.total_vocabulary}개`, label: '단어장' },
                ].map((item, i) => (
                  <View key={i} style={styles.summaryItem}>
                    <Text style={styles.summaryValue}>{item.value}</Text>
                    <Text style={styles.summaryLabel}>{item.label}</Text>
                  </View>
                ))}
              </View>

              {summary.weekly_change !== 0 && (
                <View style={styles.weeklyRow}>
                  <TrendingUp
                    size={13}
                    color={summary.weekly_change > 0 ? '#22C55E' : '#FF4D4D'}
                  />
                  <Text
                    style={[
                      styles.weeklyText,
                      { color: summary.weekly_change > 0 ? '#22C55E' : '#FF4D4D' },
                    ]}
                  >
                    지난주 대비 {summary.weekly_change > 0 ? '+' : ''}
                    {summary.weekly_change.toFixed(1)}점
                  </Text>
                </View>
              )}
            </View>
          </View>
        )}

        {!isHomeAnalysis && effectiveStats && (
          <View style={styles.section}>
            <View style={styles.sectionHead}>
              <Text style={styles.sectionEye}>SESSION</Text>
              <Text style={styles.sectionTitle}>이번 세션 요약</Text>
            </View>

            <View style={styles.card}>
              <View style={styles.sessionGrid}>
                {[
                  { value: duration || '00:00', label: '대화 시간' },
                  { value: `${effectiveStats.messageCount}`, label: '메시지 수' },
                  { value: `${effectiveStats.speakerCount}`, label: '화자 수' },
                  { value: `${rating}/5`, label: '사용자 평점' },
                ].map((item, i) => (
                  <View key={i} style={styles.sessionItem}>
                    <Text style={styles.sessionValue}>{item.value}</Text>
                    <Text style={styles.sessionLabel}>{item.label}</Text>
                  </View>
                ))}
              </View>

              {!!feedbackTags?.length && (
                <View style={styles.feedbackBlock}>
                  <Text style={styles.feedbackBlockTitle}>선택한 피드백</Text>
                  <View style={styles.tagsWrap}>
                    {feedbackTags.map((tag: string, i: number) => (
                      <Tag key={i} label={tag} variant="outline" />
                    ))}
                  </View>
                </View>
              )}

              {(sessionId || recordingUri) && (
                <View style={styles.metaWrap}>
                  {!!sessionId && <Text style={styles.metaText}>Session ID: {sessionId}</Text>}
                  {!!recordingUri && <Text style={styles.metaText}>녹음 파일이 저장되었습니다</Text>}
                </View>
              )}
            </View>
          </View>
        )}

        {!isHomeAnalysis && (
          <View style={styles.section}>
            <View style={styles.sectionHead}>
              <Text style={styles.sectionEye}>SCORES</Text>
              <Text style={styles.sectionTitle}>이번 세션 상세 점수</Text>
            </View>

            <View style={styles.card}>
              {[
                {
                  icon: <MessageCircle size={16} color="#6C3BFF" />,
                  label: '말투 정확도',
                  value: sessionScores.speechAccuracy,
                  color: '#6C3BFF',
                  detail: derivedScoreDetails.speechAccuracy,
                },
                {
                  icon: <BookOpen size={16} color="#22C55E" />,
                  label: '어휘력',
                  value: sessionScores.vocabulary,
                  color: '#22C55E',
                  detail: derivedScoreDetails.vocabulary,
                },
                {
                  icon: <TrendingUp size={16} color="#EAB308" />,
                  label: '자연스러움',
                  value: sessionScores.naturalness,
                  color: '#EAB308',
                  detail: derivedScoreDetails.naturalness,
                },
              ].map((item, i) => (
                <View key={i} style={[styles.scoreItem, i < 2 && styles.scoreItemBorder]}>
                  <View style={styles.scoreRow}>
                    <View style={styles.scoreIconWrap}>{item.icon}</View>
                    <Text style={styles.scoreLabel}>{item.label}</Text>
                    <Text style={[styles.scoreValue, { color: item.color }]}>
                      {Math.round(item.value * 100)}%
                    </Text>
                  </View>

                  <View style={styles.scoreBarTrack}>
                    <View
                      style={[
                        styles.scoreBarFill,
                        {
                          width: `${Math.round(item.value * 100)}%`,
                          backgroundColor: item.color,
                        },
                      ]}
                    />
                  </View>

                  {item.detail?.source ? (
                    <Text style={styles.scoreFootnote}>
                      {getScoreSourceLabel(item.detail)}
                      {item.detail.note ? ` · ${item.detail.note}` : ''}
                    </Text>
                  ) : null}
                </View>
              ))}

              {usedFallbackScores ? (
                <View style={styles.scoreWarning}>
                  <Text style={styles.scoreWarningText}>
                    일부 점수는 분석 실패로 기본값을 사용했습니다.
                  </Text>
                </View>
              ) : null}
            </View>
          </View>
        )}

        {!isHomeAnalysis && effectiveStats && (
          <View style={styles.section}>
            <View style={styles.sectionHead}>
              <Text style={styles.sectionEye}>INSIGHTS</Text>
              <Text style={styles.sectionTitle}>세션 인사이트</Text>
            </View>

            <View style={styles.card}>
              <View style={styles.insightHeaderRow}>
                <View style={styles.insightStat}>
                  <CheckCircle2 size={16} color="#22C55E" />
                  <Text style={styles.insightStatText}>긍정 신호 {effectiveStats.successCount}</Text>
                </View>
                <View style={styles.insightStat}>
                  <AlertTriangle size={16} color="#FF9800" />
                  <Text style={styles.insightStatText}>주의 포인트 {effectiveStats.riskCount}</Text>
                </View>
                <View style={styles.insightStat}>
                  <Star size={16} color="#6C3BFF" />
                  <Text style={styles.insightStatText}>{ratingLabel}</Text>
                </View>
              </View>

              {topSuccessInsights.length > 0 && (
                <View style={styles.insightSectionBlock}>
                  <View style={styles.inlineTitleRow}>
                    <Sparkles size={15} color="#22C55E" />
                    <Text style={styles.inlineTitle}>좋았던 점</Text>
                  </View>
                  {topSuccessInsights.map((item: Insight) => (
                    <View key={item.id} style={styles.insightItem}>
                      <Text style={styles.insightMessage}>{item.message}</Text>
                      {!!item.suggestion && (
                        <Text style={styles.insightSuggestion}>추천 표현: {item.suggestion}</Text>
                      )}
                    </View>
                  ))}
                </View>
              )}

              {topRiskInsights.length > 0 && (
                <View style={styles.insightSectionBlock}>
                  <View style={styles.inlineTitleRow}>
                    <AlertTriangle size={15} color="#FF9800" />
                    <Text style={styles.inlineTitle}>보완할 점</Text>
                  </View>
                  {topRiskInsights.map((item: Insight) => (
                    <View key={item.id} style={styles.insightItem}>
                      <Text style={styles.insightMessage}>{item.message}</Text>
                      {!!item.suggestion && (
                        <Text style={styles.insightSuggestion}>추천 표현: {item.suggestion}</Text>
                      )}
                    </View>
                  ))}
                </View>
              )}

              {topSuccessInsights.length === 0 && topRiskInsights.length === 0 && (
                <View style={styles.emptyMini}>
                  <Text style={styles.emptyMiniText}>아직 표시할 세션 인사이트가 없습니다.</Text>
                </View>
              )}
            </View>
          </View>
        )}

        {!isHomeAnalysis && finalTurns.length > 0 && (
          <View style={styles.section}>
            <View style={styles.sectionHead}>
              <Text style={styles.sectionEye}>TRANSCRIPT</Text>
              <Text style={styles.sectionTitle}>대화 기록</Text>
            </View>

            <View style={styles.card}>
              {finalTurns.slice(0, 6).map((turn: TranscriptTurn, i: number) => (
                <View
                  key={turn.id}
                  style={[styles.turnItem, i < Math.min(finalTurns.length, 6) - 1 && styles.turnItemBorder]}
                >
                  <Text style={styles.turnSpeaker}>{turn.speaker}</Text>
                  <Text style={styles.turnText}>{turn.text}</Text>
                </View>
              ))}
            </View>
          </View>
        )}

        {weakAreas.length > 0 ? (
          <View style={styles.section}>
            <View style={styles.sectionHead}>
              <Text style={styles.sectionEye}>WEAK SPOTS</Text>
              <Text style={styles.sectionTitle}>약점 분석</Text>
            </View>

            <View style={styles.card}>
              {weakAreas.slice(0, 5).map((area, i) => {
                const col = getWeakAreaColor(area.severity, i);
                const barW = Math.max(12, Math.round(((area.count || 0) / maxWeakCount) * 100));

                return (
                  <View
                    key={i}
                    style={[
                      styles.weakItem,
                      i < Math.min(weakAreas.length, 5) - 1 && styles.weakItemBorder,
                    ]}
                  >
                    <View style={[styles.weakRank, { backgroundColor: col + '18' }]}>
                      <Text style={[styles.weakRankText, { color: col }]}>{i + 1}</Text>
                    </View>

                    <View style={styles.weakInfo}>
                      <Text style={styles.weakLabel}>
                        {area.error_type_ko || area.error_type}
                      </Text>
                      <View style={styles.weakBarTrack}>
                        <View
                          style={[
                            styles.weakBarFill,
                            { width: `${barW}%`, backgroundColor: col },
                          ]}
                        />
                      </View>
                    </View>

                    <View style={[styles.weakBadge, { backgroundColor: col + '14' }]}>
                      <Text style={[styles.weakCount, { color: col }]}>{area.count}회</Text>
                    </View>
                  </View>
                );
              })}
            </View>
          </View>
        ) : isHomeAnalysis ? (
          <View style={styles.section}>
            <View style={[styles.card, styles.emptyCard]}>
              <View style={styles.emptyIcon}>
                <AlertCircle size={20} color="#6C3BFF" />
              </View>
              <Text style={styles.emptyTitle}>아직 쌓인 실수 데이터가 없어요</Text>
              <Text style={styles.emptyText}>
                대화 후 백엔드가 오류를 저장하면 이곳에 반복되는 약점이 순위로 표시됩니다.
              </Text>
            </View>
          </View>
        ) : null}

        {savedItems && savedItems.length > 0 && (
          <View style={styles.section}>
            <View style={styles.sectionHead}>
              <Text style={styles.sectionEye}>SAVED</Text>
              <Text style={styles.sectionTitle}>저장한 표현 ({savedItems.length})</Text>
            </View>
            <View style={styles.tagsWrap}>
              {savedItems.map((item: string, i: number) => (
                <Tag key={i} label={item} variant="outline" />
              ))}
            </View>
          </View>
        )}
      </ScrollView>

      <View style={styles.footer}>
        <TouchableOpacity
          style={styles.footerBtnOutline}
          onPress={() => navigation.navigate('Main', { screen: 'Home' })}
        >
          <Text style={styles.footerBtnOutlineText}>홈으로</Text>
        </TouchableOpacity>

        <TouchableOpacity
          style={styles.footerBtn}
          onPress={() => navigation.navigate('AvatarSelection')}
        >
          <Text style={styles.footerBtnText}>다시 연습하기</Text>
        </TouchableOpacity>
      </View>
    </SafeAreaView>
  );
}

// ─── Styles ───────────────────────────────────────────────────────────────────

const BRAND = '#6C3BFF';
const GREY = '#F2F2F7';
const BORDER = '#E5E5EA';

const styles = StyleSheet.create({
  safe: { flex: 1, backgroundColor: '#FFFFFF' },
  content: { paddingHorizontal: 16, paddingTop: 8, paddingBottom: 120 },

  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 14,
    paddingVertical: 12,
    borderBottomWidth: 1,
    borderBottomColor: BORDER,
  },
  headerBtn: { width: 36, alignItems: 'center' },
  headerTitle: { fontSize: 15, fontWeight: '500', color: '#111' },

  loadingWrap: { flex: 1, alignItems: 'center', justifyContent: 'center', gap: 12 },
  loadingText: { fontSize: 13, color: '#999' },

  heroCard: {
    position: 'relative',
    overflow: 'hidden',
    borderRadius: 24,
    padding: 20,
    marginBottom: 20,
    marginTop: 4,
  },
  heroBlobA: {
    position: 'absolute',
    width: 180,
    height: 180,
    borderRadius: 90,
    right: -50,
    top: -50,
    backgroundColor: 'rgba(255,255,255,0.14)',
  },
  heroBlobB: {
    position: 'absolute',
    width: 90,
    height: 90,
    borderRadius: 45,
    left: -24,
    bottom: -28,
    backgroundColor: 'rgba(255,255,255,0.10)',
  },
  heroTopRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: 16,
  },
  heroPill: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 5,
    paddingHorizontal: 10,
    paddingVertical: 6,
    borderRadius: 20,
    backgroundColor: 'rgba(255,255,255,0.20)',
  },
  heroPillText: {
    fontSize: 11,
    fontWeight: '600',
    color: '#fff',
    letterSpacing: 0.3,
  },
  heroLabel: { fontSize: 12, fontWeight: '500', color: 'rgba(255,255,255,0.85)' },
  heroTitle: {
    fontSize: 22,
    fontWeight: '700',
    color: '#fff',
    letterSpacing: -0.3,
    marginBottom: 6,
  },
  heroSub: {
    fontSize: 13,
    color: 'rgba(255,255,255,0.80)',
    lineHeight: 19,
    marginBottom: 20,
  },
  heroBottom: { flexDirection: 'row', alignItems: 'center', gap: 12 },
  heroScoreBubble: {
    width: 86,
    height: 86,
    borderRadius: 43,
    backgroundColor: '#fff',
    alignItems: 'center',
    justifyContent: 'center',
  },
  heroScore: { fontSize: 30, fontWeight: '700', letterSpacing: -1 },
  heroScoreUnit: { fontSize: 11, fontWeight: '500', marginTop: -3 },
  heroInsight: {
    flex: 1,
    padding: 13,
    borderRadius: 16,
    backgroundColor: 'rgba(255,255,255,0.18)',
  },
  heroInsightEye: {
    fontSize: 10,
    fontWeight: '500',
    color: 'rgba(255,255,255,0.70)',
    marginBottom: 4,
    letterSpacing: 0.3,
  },
  heroInsightText: {
    fontSize: 13,
    fontWeight: '600',
    color: '#fff',
    lineHeight: 18,
  },

  section: { marginBottom: 20 },
  sectionHead: { marginBottom: 10 },
  sectionEye: {
    fontSize: 10,
    fontWeight: '600',
    color: '#999',
    letterSpacing: 1,
    marginBottom: 2,
  },
  sectionTitle: { fontSize: 16, fontWeight: '600', color: '#111' },

  card: {
    backgroundColor: '#fff',
    borderRadius: 16,
    borderWidth: 1,
    borderColor: BORDER,
    overflow: 'hidden',
  },

  summaryGrid: { flexDirection: 'row', flexWrap: 'wrap' },
  summaryItem: {
    width: '50%',
    padding: 16,
    borderBottomWidth: 1,
    borderBottomColor: BORDER,
  },
  summaryValue: {
    fontSize: 17,
    fontWeight: '600',
    color: '#111',
    marginBottom: 3,
  },
  summaryLabel: { fontSize: 11, color: '#999' },
  weeklyRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 5,
    padding: 12,
    borderTopWidth: 1,
    borderTopColor: BORDER,
  },
  weeklyText: { fontSize: 12, fontWeight: '500' },

  sessionGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
  },
  sessionItem: {
    width: '50%',
    paddingHorizontal: 16,
    paddingTop: 16,
    paddingBottom: 10,
  },
  sessionValue: {
    fontSize: 18,
    fontWeight: '700',
    color: '#111',
    marginBottom: 4,
  },
  sessionLabel: {
    fontSize: 11,
    color: '#999',
  },
  feedbackBlock: {
    paddingHorizontal: 16,
    paddingBottom: 16,
    paddingTop: 8,
  },
  feedbackBlockTitle: {
    fontSize: 12,
    fontWeight: '600',
    color: '#666',
    marginBottom: 10,
  },
  metaWrap: {
    paddingHorizontal: 16,
    paddingBottom: 16,
    gap: 4,
  },
  metaText: {
    fontSize: 11,
    color: '#888',
  },

  scoreItem: { padding: 14 },
  scoreItemBorder: { borderBottomWidth: 1, borderBottomColor: BORDER },
  scoreRow: { flexDirection: 'row', alignItems: 'center', marginBottom: 8 },
  scoreIconWrap: {
    width: 28,
    height: 28,
    borderRadius: 8,
    backgroundColor: GREY,
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: 10,
  },
  scoreLabel: { flex: 1, fontSize: 14, fontWeight: '500', color: '#111' },
  scoreValue: { fontSize: 14, fontWeight: '600' },
  scoreBarTrack: {
    height: 5,
    borderRadius: 3,
    backgroundColor: BORDER,
    overflow: 'hidden',
  },
  scoreBarFill: { height: '100%', borderRadius: 3 },
  scoreFootnote: {
    marginTop: 8,
    fontSize: 11,
    color: '#777',
    lineHeight: 16,
  },
  scoreWarning: {
    margin: 14,
    marginTop: 0,
    padding: 10,
    borderRadius: 10,
    backgroundColor: '#FFF4E5',
  },
  scoreWarningText: {
    fontSize: 11,
    color: '#A05A00',
    lineHeight: 16,
  },

  insightHeaderRow: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 10,
    padding: 14,
    borderBottomWidth: 1,
    borderBottomColor: BORDER,
  },
  insightStat: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    backgroundColor: '#F8F8FC',
    paddingHorizontal: 10,
    paddingVertical: 8,
    borderRadius: 20,
  },
  insightStatText: {
    fontSize: 12,
    fontWeight: '600',
    color: '#333',
  },
  insightSectionBlock: {
    padding: 14,
    borderBottomWidth: 1,
    borderBottomColor: BORDER,
  },
  inlineTitleRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    marginBottom: 10,
  },
  inlineTitle: {
    fontSize: 13,
    fontWeight: '700',
    color: '#111',
  },
  insightItem: {
    backgroundColor: '#FAFAFD',
    borderRadius: 12,
    padding: 12,
    marginBottom: 8,
  },
  insightMessage: {
    fontSize: 13,
    fontWeight: '600',
    color: '#222',
    lineHeight: 18,
    marginBottom: 4,
  },
  insightSuggestion: {
    fontSize: 12,
    color: '#666',
    lineHeight: 17,
  },
  emptyMini: {
    padding: 16,
    alignItems: 'center',
  },
  emptyMiniText: {
    fontSize: 12,
    color: '#888',
  },

  turnItem: {
    padding: 14,
  },
  turnItemBorder: {
    borderBottomWidth: 1,
    borderBottomColor: BORDER,
  },
  turnSpeaker: {
    fontSize: 11,
    fontWeight: '700',
    color: '#6C3BFF',
    marginBottom: 6,
  },
  turnText: {
    fontSize: 13,
    color: '#222',
    lineHeight: 20,
  },

  weakItem: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
    padding: 14,
  },
  weakItemBorder: { borderBottomWidth: 1, borderBottomColor: BORDER },
  weakRank: {
    width: 32,
    height: 32,
    borderRadius: 16,
    alignItems: 'center',
    justifyContent: 'center',
  },
  weakRankText: { fontSize: 13, fontWeight: '600' },
  weakInfo: { flex: 1, gap: 6 },
  weakLabel: { fontSize: 13, fontWeight: '500', color: '#111' },
  weakBarTrack: {
    height: 4,
    borderRadius: 2,
    backgroundColor: BORDER,
    overflow: 'hidden',
  },
  weakBarFill: { height: '100%', borderRadius: 2 },
  weakBadge: {
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 20,
  },
  weakCount: { fontSize: 11, fontWeight: '600' },

  emptyCard: {
    alignItems: 'center',
    paddingVertical: 28,
    paddingHorizontal: 20,
  },
  emptyIcon: {
    width: 44,
    height: 44,
    borderRadius: 22,
    backgroundColor: 'rgba(108,59,255,0.10)',
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 12,
  },
  emptyTitle: {
    fontSize: 14,
    fontWeight: '600',
    color: '#111',
    marginBottom: 6,
  },
  emptyText: {
    fontSize: 12,
    color: '#999',
    lineHeight: 18,
    textAlign: 'center',
  },

  tagsWrap: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 8,
  },

  footer: {
    position: 'absolute',
    bottom: 0,
    left: 0,
    right: 0,
    flexDirection: 'row',
    gap: 10,
    padding: 16,
    backgroundColor: '#fff',
    borderTopWidth: 1,
    borderTopColor: BORDER,
  },
  footerBtnOutline: {
    flex: 1,
    paddingVertical: 13,
    borderRadius: 22,
    borderWidth: 1,
    borderColor: BORDER,
    alignItems: 'center',
  },
  footerBtnOutlineText: {
    fontSize: 14,
    fontWeight: '500',
    color: '#111',
  },
  footerBtn: {
    flex: 1,
    paddingVertical: 13,
    borderRadius: 22,
    backgroundColor: BRAND,
    alignItems: 'center',
  },
  footerBtnText: {
    fontSize: 14,
    fontWeight: '500',
    color: '#fff',
  },
});
