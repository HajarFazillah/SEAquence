import React, { useState, useEffect } from 'react';
import { View, Text, StyleSheet, ScrollView, ActivityIndicator } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useNavigation, useRoute } from '@react-navigation/native';
import {
  TrendingUp, CheckCircle, AlertCircle,
  BookOpen, MessageCircle, Target, Flame,
} from 'lucide-react-native';
import { Header, Card, Button, ProgressBar, Icon, Tag } from '../components';
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

export default function AnalyticsScreen() {
  const navigation = useNavigation<any>();
  const route      = useRoute<any>();
  const { avatar, duration, scores, savedItems } = route.params || {};

  const [loading, setLoading]   = useState(true);
  const [summary, setSummary]   = useState<AnalyticsSummary | null>(null);
  const [weakAreas, setWeakAreas] = useState<WeakArea[]>([]);
  const [recommendations, setRecommendations] = useState<string[]>([]);

  useEffect(() => {
    loadAnalytics();
  }, []);

  const loadAnalytics = async () => {
    try {
      setLoading(true);
      const userId = await AsyncStorage.getItem('user_id') || 'test-user-1';

      // 병렬 호출
      const [summaryRes, weakRes, recRes] = await Promise.allSettled([
        fetch(`${AI_SERVER}/api/v1/analytics/${userId}/summary`),
        fetch(`${AI_SERVER}/api/v1/analytics/${userId}/weak-areas`),
        fetch(`${AI_SERVER}/api/v1/analytics/${userId}/recommendations`),
      ]);

      if (summaryRes.status === 'fulfilled' && summaryRes.value.ok) {
        setSummary(await summaryRes.value.json());
      }
      if (weakRes.status === 'fulfilled' && weakRes.value.ok) {
        const data = await weakRes.value.json();
        setWeakAreas(Array.isArray(data) ? data : []);
      }
      if (recRes.status === 'fulfilled' && recRes.value.ok) {
        const data = await recRes.value.json();
        setRecommendations(data.recommendations || data.topics || []);
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

  const handleGoHome = () => {
    navigation.navigate('Main', { screen: 'Home' });
  };

  const handlePracticeAgain = () => {
    navigation.navigate('AvatarSelection');
  };

  if (loading) {
    return (
      <SafeAreaView style={styles.safe} edges={['top']}>
        <Header title="분석 결과" showBack={false} />
        <View style={styles.loadingContainer}>
          <ActivityIndicator size="large" color="#6C3BFF" />
          <Text style={styles.loadingText}>분석 중...</Text>
        </View>
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView style={styles.safe} edges={['top']}>
      <Header title="분석 결과" showBack={false} />

      <ScrollView contentContainerStyle={styles.content} showsVerticalScrollIndicator={false}>

        {/* ── 이번 세션 종합 점수 ── */}
        <Card variant="elevated" style={styles.overallCard}>
          <Text style={styles.overallLabel}>이번 세션 종합 점수</Text>
          <Text style={styles.overallScore}>{overallScore}점</Text>
          <Text style={styles.overallDesc}>
            {avatar?.name_ko || '아바타'}와 {duration || '5분'} 동안 대화했어요
          </Text>
        </Card>

        {/* ── 누적 학습 현황 (AI 서버) ── */}
        {summary && (
          <Card variant="elevated" style={styles.summaryCard}>
            <Text style={styles.sectionTitle}>누적 학습 현황</Text>
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

        {/* ── 약점 분석 (AI 서버) ── */}
        {weakAreas.length > 0 && (
          <>
            <Text style={styles.sectionTitle}>약점 분석</Text>
            <Card variant="elevated" style={styles.weakCard}>
              {weakAreas.slice(0, 5).map((area, i) => (
                <View key={i} style={styles.weakItem}>
                  <AlertCircle size={16} color="#E53935" />
                  <View style={styles.weakInfo}>
                    <Text style={styles.weakLabel}>{area.error_type_ko || area.error_type}</Text>
                    <Text style={styles.weakCount}>{area.count}회 오류</Text>
                  </View>
                </View>
              ))}
            </Card>
          </>
        )}

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

        {/* ── 다음 추천 (AI 서버 or 기본값) ── */}
        <Text style={styles.sectionTitle}>다음 추천 연습</Text>
        <View style={styles.suggestedTags}>
          {(recommendations.length > 0
            ? recommendations
            : ['일상 대화', '카페 주문', '자기소개']
          ).map((topic: string, i: number) => (
            <Tag key={i} label={topic} variant="outline" />
          ))}
        </View>

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
  safe:             { flex: 1, backgroundColor: '#F7F7FB' },
  content:          { paddingHorizontal: 20, paddingBottom: 120 },
  loadingContainer: { flex: 1, alignItems: 'center', justifyContent: 'center' },
  loadingText:      { marginTop: 12, fontSize: 14, color: '#6C6C80' },

  overallCard:  { alignItems: 'center', backgroundColor: '#6C3BFF', marginBottom: 20 },
  overallLabel: { fontSize: 14, color: 'rgba(255,255,255,0.8)', marginBottom: 8 },
  overallScore: { fontSize: 48, fontWeight: '700', color: '#FFFFFF', marginBottom: 4 },
  overallDesc:  { fontSize: 14, color: 'rgba(255,255,255,0.8)' },

  summaryCard: { marginBottom: 20 },
  summaryGrid: { flexDirection: 'row', flexWrap: 'wrap', gap: 12, marginBottom: 8 },
  summaryItem: { flex: 1, minWidth: '40%', alignItems: 'center', padding: 12, backgroundColor: '#F5F5FA', borderRadius: 12 },
  summaryValue: { fontSize: 18, fontWeight: '700', color: '#1A1A2E', marginBottom: 4 },
  summaryLabel: { fontSize: 11, color: '#6C6C80' },
  weeklyChange: { flexDirection: 'row', alignItems: 'center', gap: 4, marginTop: 4 },
  weeklyChangeText: { fontSize: 12, fontWeight: '600' },

  sectionTitle: { fontSize: 16, fontWeight: '700', color: '#1A1A2E', marginBottom: 12 },

  scoresCard: { marginBottom: 20 },
  scoreItem:  { marginBottom: 16 },
  scoreHeader: { flexDirection: 'row', alignItems: 'center', marginBottom: 8 },
  scoreLabel:  { flex: 1, fontSize: 14, color: '#1A1A2E', marginLeft: 8 },
  scoreValue:  { fontSize: 14, fontWeight: '700', color: '#1A1A2E' },

  weakCard: { marginBottom: 20 },
  weakItem: { flexDirection: 'row', alignItems: 'center', gap: 10, marginBottom: 12 },
  weakInfo: { flex: 1 },
  weakLabel: { fontSize: 14, color: '#1A1A2E', fontWeight: '600' },
  weakCount: { fontSize: 12, color: '#6C6C80' },

  savedTags:     { flexDirection: 'row', flexWrap: 'wrap', gap: 8, marginBottom: 20 },
  suggestedTags: { flexDirection: 'row', flexWrap: 'wrap', gap: 8, marginBottom: 20 },

  footer:           { position: 'absolute', bottom: 0, left: 0, right: 0, padding: 20, backgroundColor: '#F7F7FB', flexDirection: 'row', gap: 12 },
  footerBtnOutline: { flex: 1 },
  footerBtn:        { flex: 1 },
});