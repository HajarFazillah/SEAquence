import React, { useState, useEffect } from 'react';
import { View, Text, StyleSheet, ScrollView, ActivityIndicator } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useNavigation, useRoute } from '@react-navigation/native';
import {
  TrendingUp, AlertCircle,
  BookOpen, MessageCircle, Target,
} from 'lucide-react-native';
import { Header, Card, Button, ProgressBar, Tag } from '../components';
import AsyncStorage from '@react-native-async-storage/async-storage';

// ── AI 서버 주소 ──────────────────────────────────────────────────────────────
const AI_SERVER = 'http://10.0.2.2:8000';

// ── 타입 ─────────────────────────────────────────────────────────────────────
interface AnalyticsSummary {
  overall_score:        number;
  proficiency_level_ko: string;
  current_streak:       number;
  streak_emoji:         string;
  weekly_change:        number;
  total_vocabulary:     number;
  total_conversations:  number;
}

interface WeakArea {
  error_type:    string;
  error_type_ko: string;
  count:         number;
  severity:      string;
}

const getScoreTone = (score: number) => {
  if (score >= 85) return { color: '#3D8B6D', label: '아주 좋아요' };
  if (score >= 70) return { color: '#5E55D6', label: '꾸준히 성장 중' };
  return { color: '#C86B2C', label: '집중 연습 추천' };
};

const getWeakAreaColor = (severity: string, index: number) => {
  if (severity === 'high' || severity === 'error') return '#E53935';
  if (severity === 'medium' || severity === 'warning') return '#F4A261';
  return ['#6C3BFF', '#3F51B5', '#009688'][index % 3];
};

export default function AnalyticsScreen() {
  const navigation = useNavigation<any>();
  const route      = useRoute<any>();
  const { avatar, duration, scores, savedItems, source } = route.params || {};
  const isHomeAnalysis = source === 'home' || (!avatar && !duration && !scores);

  const [loading, setLoading]   = useState(true);
  const [summary, setSummary]   = useState<AnalyticsSummary | null>(null);
  const [weakAreas, setWeakAreas] = useState<WeakArea[]>([]);

  useEffect(() => {
    loadAnalytics();
  }, []);

  const loadAnalytics = async () => {
    try {
      setLoading(true);
      const userId = await AsyncStorage.getItem('user_id') || 'test-user-1';

      // 병렬 호출
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

  // 이번 세션 점수 (ConversationSummaryScreen에서 전달)
  const sessionScores = {
    speechAccuracy: scores?.speechAccuracy ?? 0.80,
    vocabulary:     scores?.vocabulary     ?? 0.72,
    naturalness:    scores?.naturalness    ?? 0.78,
  };

  const overallScore = Math.round(
    (sessionScores.speechAccuracy + sessionScores.vocabulary + sessionScores.naturalness) / 3 * 100
  );
  const displayScore = isHomeAnalysis ? Math.round(summary?.overall_score || 0) : overallScore;
  const hasSummaryScore = Boolean(summary || !isHomeAnalysis);
  const scoreTone = hasSummaryScore ? getScoreTone(displayScore) : { color: '#5E55D6', label: '준비 중' };
  const maxWeakCount = Math.max(1, ...weakAreas.map(area => area.count || 0));
  const heroMetricValue = hasSummaryScore
    ? displayScore
    : weakAreas.length > 0
      ? weakAreas.length
      : '준비';
  const heroMetricUnit = hasSummaryScore
    ? '점'
    : weakAreas.length > 0
      ? '개 약점'
      : '데이터';

  const handleGoHome = () => {
    navigation.navigate('Main', { screen: 'Home' });
  };

  const handlePracticeAgain = () => {
    navigation.navigate('AvatarSelection');
  };

  if (loading) {
    return (
      <SafeAreaView style={styles.safe} edges={['top']}>
        <Header title={isHomeAnalysis ? '실수 분석' : '분석 결과'} showBack={false} />
        <View style={styles.loadingContainer}>
          <View style={styles.loadingOrb}>
            <ActivityIndicator size="large" color="#FFFFFF" />
          </View>
          <Text style={styles.loadingText}>분석 중...</Text>
        </View>
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView style={styles.safe} edges={['top']}>
      <Header title={isHomeAnalysis ? '실수 분석' : '분석 결과'} showBack={false} />

      <ScrollView contentContainerStyle={styles.content} showsVerticalScrollIndicator={false}>

        {/* ── 종합 리포트 ── */}
        <View style={[styles.heroCard, { backgroundColor: scoreTone.color }]}>
          <View style={styles.heroBlobLarge} />
          <View style={styles.heroBlobSmall} />
          <View style={styles.heroTopRow}>
            <View style={styles.heroPill}>
              <Target size={13} color="#FFFFFF" />
              <Text style={styles.heroPillText}>
                {isHomeAnalysis ? 'Mistake Report' : 'Session Report'}
              </Text>
            </View>
            <Text style={styles.heroStatus}>{scoreTone.label}</Text>
          </View>

          <Text style={styles.heroTitle}>
            {isHomeAnalysis ? '실수 패턴을 한눈에 봐요' : '이번 대화가 이렇게 쌓였어요'}
          </Text>
          <Text style={styles.heroSubtitle}>
            {isHomeAnalysis
              ? '이전 대화의 반복 실수와 다음 연습 방향을 정리합니다.'
              : `${avatar?.name_ko || '아바타'}와 ${duration || '5분'} 동안 연습한 결과입니다.`}
          </Text>

          <View style={styles.heroScoreRow}>
            <View style={styles.heroScoreBubble}>
              <Text style={styles.heroScore}>{heroMetricValue}</Text>
              <Text style={styles.heroScoreUnit}>{heroMetricUnit}</Text>
            </View>
            <View style={styles.heroInsight}>
              <Text style={styles.heroInsightLabel}>오늘의 포커스</Text>
              <Text style={styles.heroInsightText}>
                {weakAreas[0]?.error_type_ko || weakAreas[0]?.error_type || '대화 후 실수 패턴 분석'}
              </Text>
            </View>
          </View>
        </View>

        {/* ── 누적 학습 현황 (AI 서버) ── */}
        {summary && (
          <Card variant="elevated" style={styles.summaryCard}>
            <View style={styles.sectionHeader}>
              <Text style={styles.sectionEyebrow}>Progress</Text>
              <Text style={styles.sectionTitle}>누적 학습 현황</Text>
            </View>
            <View style={styles.summaryGrid}>
              <View style={styles.summaryItem}>
                <Text style={styles.summaryValue}>{summary.proficiency_level_ko}</Text>
                <Text style={styles.summaryLabel}>현재 수준</Text>
              </View>
              <View style={styles.summaryItem}>
                <Text style={styles.summaryValue}>
                  {summary.streak_emoji} {summary.current_streak}일
                </Text>
                <Text style={styles.summaryLabel}>연속 학습</Text>
              </View>
              <View style={styles.summaryItem}>
                <Text style={styles.summaryValue}>{summary.total_conversations}회</Text>
                <Text style={styles.summaryLabel}>총 대화</Text>
              </View>
              <View style={styles.summaryItem}>
                <Text style={styles.summaryValue}>{summary.total_vocabulary}개</Text>
                <Text style={styles.summaryLabel}>단어장</Text>
              </View>
            </View>
            {summary.weekly_change !== 0 && (
              <View style={styles.weeklyChange}>
                <TrendingUp size={14} color={summary.weekly_change > 0 ? '#4CAF50' : '#E53935'} />
                <Text style={[
                  styles.weeklyChangeText,
                  { color: summary.weekly_change > 0 ? '#4CAF50' : '#E53935' }
                ]}>
                  지난주 대비 {summary.weekly_change > 0 ? '+' : ''}{summary.weekly_change.toFixed(1)}점
                </Text>
              </View>
            )}
          </Card>
        )}

        {/* ── 이번 세션 상세 점수 ── */}
        {!isHomeAnalysis && (
          <>
            <Text style={styles.sectionTitle}>이번 세션 상세 점수</Text>
            <Card variant="elevated" style={styles.scoresCard}>
              <View style={styles.scoreItem}>
                <View style={styles.scoreHeader}>
                  <MessageCircle size={18} color="#6C3BFF" />
                  <Text style={styles.scoreLabel}>말투 정확도</Text>
                  <Text style={styles.scoreValue}>{Math.round(sessionScores.speechAccuracy * 100)}%</Text>
                </View>
                <ProgressBar progress={sessionScores.speechAccuracy} color="#6C3BFF" />
              </View>
              <View style={styles.scoreItem}>
                <View style={styles.scoreHeader}>
                  <BookOpen size={18} color="#4CAF50" />
                  <Text style={styles.scoreLabel}>어휘력</Text>
                  <Text style={styles.scoreValue}>{Math.round(sessionScores.vocabulary * 100)}%</Text>
                </View>
                <ProgressBar progress={sessionScores.vocabulary} color="#4CAF50" />
              </View>
              <View style={styles.scoreItem}>
                <View style={styles.scoreHeader}>
                  <TrendingUp size={18} color="#F4A261" />
                  <Text style={styles.scoreLabel}>자연스러움</Text>
                  <Text style={styles.scoreValue}>{Math.round(sessionScores.naturalness * 100)}%</Text>
                </View>
                <ProgressBar progress={sessionScores.naturalness} color="#F4A261" />
              </View>
            </Card>
          </>
        )}

        {/* ── 약점 분석 (AI 서버) ── */}
        {weakAreas.length > 0 ? (
          <>
            <View style={styles.sectionHeader}>
              <Text style={styles.sectionEyebrow}>Weak Spots</Text>
              <Text style={styles.sectionTitle}>약점 분석</Text>
            </View>
            <Card variant="elevated" style={styles.weakCard}>
              {weakAreas.slice(0, 5).map((area, i) => (
                <View key={i} style={styles.weakItem}>
                  <View style={[styles.weakRank, { backgroundColor: getWeakAreaColor(area.severity, i) + '18' }]}>
                    <Text style={[styles.weakRankText, { color: getWeakAreaColor(area.severity, i) }]}>{i + 1}</Text>
                  </View>
                  <View style={styles.weakInfo}>
                    <Text style={styles.weakLabel}>{area.error_type_ko || area.error_type}</Text>
                    <View style={styles.weakBarTrack}>
                      <View
                        style={[
                          styles.weakBarFill,
                          {
                            width: `${Math.max(12, Math.round(((area.count || 0) / maxWeakCount) * 100))}%`,
                            backgroundColor: getWeakAreaColor(area.severity, i),
                          },
                        ]}
                      />
                    </View>
                  </View>
                  <View style={styles.weakCountBadge}>
                    <Text style={styles.weakCount}>{area.count}회</Text>
                  </View>
                </View>
              ))}
            </Card>
          </>
        ) : isHomeAnalysis ? (
          <Card variant="elevated" style={styles.emptyWeakCard}>
            <View style={styles.emptyIcon}>
              <AlertCircle size={20} color="#6C3BFF" />
            </View>
            <Text style={styles.emptyTitle}>아직 쌓인 실수 데이터가 없어요</Text>
            <Text style={styles.emptyText}>
              대화 후 백엔드가 오류를 저장하면 이곳에 반복되는 약점이 순위로 표시됩니다.
            </Text>
          </Card>
        ) : null}

        {/* ── 저장한 단어 (ConversationSummaryScreen에서 전달) ── */}
        {savedItems && savedItems.length > 0 && (
          <>
            <Text style={styles.sectionTitle}>저장한 표현 ({savedItems.length})</Text>
            <View style={styles.savedTags}>
              {savedItems.map((item: string, i: number) => (
                <Tag key={i} label={item} variant="outline" />
              ))}
            </View>
          </>
        )}

      </ScrollView>

      {/* Footer */}
      <View style={styles.footer}>
        <Button
          title="홈으로"
          onPress={handleGoHome}
          variant="outline"
          style={styles.footerBtnOutline}
        />
        <Button
          title="다시 연습하기"
          onPress={handlePracticeAgain}
          style={styles.footerBtn}
        />
      </View>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safe:    { flex: 1, backgroundColor: '#F3F1EA' },
  content: { paddingHorizontal: 20, paddingBottom: 126, paddingTop: 4 },

  loadingContainer: { flex: 1, alignItems: 'center', justifyContent: 'center' },
  loadingOrb:       { width: 70, height: 70, borderRadius: 35, alignItems: 'center', justifyContent: 'center', backgroundColor: '#6C3BFF', shadowColor: '#6C3BFF', shadowOffset: { width: 0, height: 12 }, shadowOpacity: 0.24, shadowRadius: 18, elevation: 6 },
  loadingText:      { marginTop: 16, fontSize: 14, fontWeight: '600', color: '#6C6C80' },

  heroCard:      { position: 'relative', overflow: 'hidden', borderRadius: 28, padding: 22, marginBottom: 22, shadowColor: '#1A1A2E', shadowOffset: { width: 0, height: 14 }, shadowOpacity: 0.16, shadowRadius: 24, elevation: 8 },
  heroBlobLarge: { position: 'absolute', width: 190, height: 190, borderRadius: 95, right: -58, top: -54, backgroundColor: 'rgba(255,255,255,0.16)' },
  heroBlobSmall: { position: 'absolute', width: 96, height: 96, borderRadius: 48, left: -30, bottom: -32, backgroundColor: 'rgba(255,255,255,0.12)' },
  heroTopRow:    { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', marginBottom: 18 },
  heroPill:      { flexDirection: 'row', alignItems: 'center', gap: 6, paddingHorizontal: 11, paddingVertical: 7, borderRadius: 999, backgroundColor: 'rgba(255,255,255,0.18)' },
  heroPillText:  { fontSize: 11, fontWeight: '800', color: '#FFFFFF', letterSpacing: 0.4 },
  heroStatus:    { fontSize: 12, fontWeight: '700', color: 'rgba(255,255,255,0.84)' },
  heroTitle:     { fontSize: 24, fontWeight: '800', color: '#FFFFFF', letterSpacing: -0.4, marginBottom: 7 },
  heroSubtitle:  { maxWidth: '92%', fontSize: 13, color: 'rgba(255,255,255,0.82)', lineHeight: 20, marginBottom: 22 },
  heroScoreRow:  { flexDirection: 'row', alignItems: 'center', gap: 14 },
  heroScoreBubble: { width: 94, height: 94, borderRadius: 47, alignItems: 'center', justifyContent: 'center', backgroundColor: 'rgba(255,255,255,0.96)' },
  heroScore:     { fontSize: 34, fontWeight: '900', color: '#1A1A2E', letterSpacing: -1 },
  heroScoreUnit: { marginTop: -4, fontSize: 11, fontWeight: '800', color: '#6C6C80' },
  heroInsight:   { flex: 1, padding: 14, borderRadius: 18, backgroundColor: 'rgba(255,255,255,0.16)' },
  heroInsightLabel: { fontSize: 11, fontWeight: '800', color: 'rgba(255,255,255,0.72)', marginBottom: 4 },
  heroInsightText:  { fontSize: 14, fontWeight: '800', color: '#FFFFFF', lineHeight: 19 },

  sectionHeader: { marginBottom: 12 },
  sectionEyebrow: { fontSize: 10, fontWeight: '800', color: '#9A8F75', letterSpacing: 1.2, textTransform: 'uppercase', marginBottom: 3 },
  sectionTitle:  { fontSize: 17, fontWeight: '800', color: '#1A1A2E', letterSpacing: -0.2 },

  summaryCard: { marginBottom: 22, borderRadius: 22 },
  summaryGrid: { flexDirection: 'row', flexWrap: 'wrap', gap: 10, marginBottom: 8 },
  summaryItem: { flex: 1, minWidth: '42%', padding: 14, backgroundColor: '#F8F6EF', borderRadius: 18, borderWidth: 1, borderColor: '#EEE8DA' },
  summaryValue: { fontSize: 18, fontWeight: '900', color: '#1A1A2E', marginBottom: 5 },
  summaryLabel: { fontSize: 11, fontWeight: '600', color: '#7B725F' },
  weeklyChange: { alignSelf: 'flex-start', flexDirection: 'row', alignItems: 'center', gap: 5, marginTop: 6, paddingHorizontal: 10, paddingVertical: 7, borderRadius: 999, backgroundColor: '#F8F6EF' },
  weeklyChangeText: { fontSize: 12, fontWeight: '700' },

  scoresCard:  { marginBottom: 22, borderRadius: 22 },
  scoreItem:   { marginBottom: 17 },
  scoreHeader: { flexDirection: 'row', alignItems: 'center', marginBottom: 9 },
  scoreLabel:  { flex: 1, fontSize: 14, fontWeight: '700', color: '#1A1A2E', marginLeft: 8 },
  scoreValue:  { fontSize: 14, fontWeight: '900', color: '#1A1A2E' },

  weakCard:       { marginBottom: 22, borderRadius: 22 },
  weakItem:       { flexDirection: 'row', alignItems: 'center', gap: 12, paddingVertical: 10, borderBottomWidth: 1, borderBottomColor: '#F0ECDF' },
  weakRank:       { width: 34, height: 34, borderRadius: 17, alignItems: 'center', justifyContent: 'center' },
  weakRankText:   { fontSize: 14, fontWeight: '900' },
  weakInfo:       { flex: 1 },
  weakLabel:      { fontSize: 14, color: '#1A1A2E', fontWeight: '800', marginBottom: 7 },
  weakBarTrack:   { height: 7, borderRadius: 999, backgroundColor: '#EEE8DA', overflow: 'hidden' },
  weakBarFill:    { height: '100%', borderRadius: 999 },
  weakCountBadge: { paddingHorizontal: 9, paddingVertical: 6, borderRadius: 999, backgroundColor: '#F8F6EF' },
  weakCount:      { fontSize: 11, fontWeight: '800', color: '#6C6C80' },

  emptyWeakCard: { alignItems: 'center', marginBottom: 22, paddingVertical: 24, borderRadius: 22 },
  emptyIcon:     { width: 46, height: 46, borderRadius: 23, alignItems: 'center', justifyContent: 'center', backgroundColor: '#F0EDFF', marginBottom: 12 },
  emptyTitle:    { fontSize: 15, fontWeight: '800', color: '#1A1A2E', marginBottom: 6 },
  emptyText:     { fontSize: 12, color: '#6C6C80', lineHeight: 18, textAlign: 'center' },

  savedTags: { flexDirection: 'row', flexWrap: 'wrap', gap: 8, marginBottom: 22 },

  footer:           { position: 'absolute', bottom: 0, left: 0, right: 0, padding: 20, backgroundColor: 'rgba(243,241,234,0.96)', flexDirection: 'row', gap: 12, borderTopWidth: 1, borderTopColor: '#E8E0CF' },
  footerBtnOutline: { flex: 1 },
  footerBtn:        { flex: 1 },
});
